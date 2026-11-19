"""The only STT client we need.

Deliberately request/response, not a duplex stream. Whisper is an
encoder-decoder over a 30 s window and IndicConformer ships as an offline
checkpoint with no cache-aware streaming decoder -- neither can emit partial
hypotheses. Our design is VAD-segmented pseudo-streaming: the transport detects
an endpoint, we send the segment, we get a final transcript. A "streaming" API
in front of that would be decoration.
"""

import httpx

from gotiny.core.errors import ProviderError, ProviderUnavailable, UnsupportedLanguage
from gotiny.providers.caps import ProviderCaps, ProviderHealth
from gotiny.providers.registry import register
from gotiny.providers.wire import WIRE_VERSION, STTRequest, STTResponse

REQUEST_HEADER = "x-gotiny-request"


@register("gotiny-stt-http@1.0", "stt")
class HTTPSTTBackend:
    def __init__(self, *, base_url: str, caps: ProviderCaps, timeout: float = 60.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self.caps = caps

    @classmethod
    def discover(cls, base_url: str, timeout: float = 3.0) -> "HTTPSTTBackend":
        """Read capabilities from the server rather than hardcoding them.

        A client that hardcodes caps will eventually disagree with the server,
        and the disagreement surfaces as mysterious failures.
        """
        base = base_url.replace("ws://", "http://").replace("wss://", "https://").rstrip("/")
        try:
            r = httpx.get(f"{base}/{WIRE_VERSION}/caps", timeout=timeout)
            r.raise_for_status()
        except httpx.HTTPError as e:
            # Translate transport failures into our taxonomy here, not 40 frames
            # deep in httpx. "The server is not running" is the single most common
            # thing that goes wrong locally and it deserves one readable line.
            raise ProviderUnavailable(
                f"no STT server reachable at {base} ({type(e).__name__}). "
                f"Start it with `just stt`."
            ) from e
        backends = r.json()["backends"]
        if not backends:
            raise ProviderUnavailable(f"{base_url} reports no backends")
        return cls(
            base_url=base,
            # Not backends[0]: see ProviderCaps.fleet.
            caps=ProviderCaps.fleet([ProviderCaps.model_validate(b) for b in backends]),
        )

    async def transcribe(self, audio: bytes, req: STTRequest) -> STTResponse:
        if not self.caps.supports(req.language):
            # A routing bug, not a transient fault. Do not pay a round trip.
            raise UnsupportedLanguage(
                f"{self.caps.name} does not serve {req.language}; "
                f"serves {sorted(self.caps.languages)}"
            )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as c:
                r = await c.post(
                    f"{self._base}/{WIRE_VERSION}/stt",
                    content=audio,
                    headers={
                        "content-type": "application/octet-stream",
                        REQUEST_HEADER: req.model_dump_json(),
                    },
                )
        except httpx.HTTPError as e:
            raise ProviderUnavailable(f"{self.caps.name}: {e}") from e

        # Status codes carry the same taxonomy as the TTS error frame: 422 is
        # "never retry this", 503 is "the box is unwell, failover may help".
        if r.status_code == 422:
            raise UnsupportedLanguage(f"{self.caps.name}: {_detail(r)}")
        if r.status_code == 503:
            raise ProviderUnavailable(f"{self.caps.name}: {_detail(r)}")
        if r.status_code >= 400:
            raise ProviderError(f"{self.caps.name}: HTTP {r.status_code} {_detail(r)}")
        return STTResponse.model_validate(r.json())

    async def health(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                r = await c.get(f"{self._base}/health")
                return ProviderHealth(name=self.caps.name, healthy=r.status_code == 200)
        except httpx.HTTPError as e:
            return ProviderHealth(name=self.caps.name, healthy=False, detail=str(e))


def _detail(r: httpx.Response) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except Exception:  # noqa: BLE001
        return r.text[:200]
