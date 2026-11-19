"""The only TTS client we need.

One client, any backend: which model answers is decided *server-side* by the
router (preset voice -> Lane A, cloned voice -> Lane B). Adding Qwen3-TTS as a
benchmark baseline is a backend file plus a config line -- no new client.
"""

from collections.abc import AsyncIterator

import httpx
import websockets

from gotiny.core.errors import (
    ProviderError,
    ProviderUnavailable,
    UnsupportedCapability,
    UnsupportedLanguage,
)
from gotiny.providers.caps import ProviderCaps, ProviderHealth
from gotiny.providers.registry import register
from gotiny.providers.wire import (
    WIRE_VERSION,
    AudioChunk,
    StreamDone,
    TTSCancel,
    TTSError,
    TTSEvent,
    TTSRequest,
    TTSTrailer,
)

_KIND_TO_EXC = {
    "unsupported_language": UnsupportedLanguage,
    "unsupported_capability": UnsupportedCapability,
    "unknown_voice": ProviderError,
    "internal": ProviderError,
}


@register("gotiny-tts-http@1.0", "tts")
class HTTPTTSBackend:
    """Speaks the v1 wire protocol over WebSocket."""

    def __init__(self, *, base_url: str, caps: ProviderCaps, timeout: float = 60.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self.caps = caps
        self._sockets: dict[str, websockets.ClientConnection] = {}

    @classmethod
    def discover(cls, base_url: str, timeout: float = 3.0) -> "HTTPTTSBackend":
        """Read capabilities from the server rather than hardcoding them.

        A client that hardcodes caps will eventually disagree with the server,
        and the disagreement shows up as mysterious synthesis failures.
        """
        http = base_url.replace("ws://", "http://").replace("wss://", "https://").rstrip("/")
        try:
            r = httpx.get(f"{http}/{WIRE_VERSION}/caps", timeout=timeout)
            r.raise_for_status()
        except httpx.HTTPError as e:
            # Translate transport failures into our taxonomy here, not 40 frames
            # deep in httpx. "The server is not running" is the single most common
            # thing that goes wrong locally and it deserves one readable line.
            raise ProviderUnavailable(
                f"no TTS server reachable at {http} ({type(e).__name__}). "
                f"Start it with `just tts`."
            ) from e
        backends = r.json()["backends"]
        if not backends:
            raise ProviderUnavailable(f"{base_url} reports no backends")
        return cls(
            base_url=base_url,
            # Not backends[0]: with two backends loaded that silently adopted
            # one model's languages as the whole server's, and which one
            # depended on dict ordering.
            caps=ProviderCaps.fleet([ProviderCaps.model_validate(b) for b in backends]),
        )

    @property
    def _url(self) -> str:
        return f"{self._base}/{WIRE_VERSION}/tts:stream"

    async def stream(self, req: TTSRequest) -> AsyncIterator[TTSEvent]:
        if not self.caps.supports(req.language):
            # A routing bug, not a transient fault. Never retry this, and do not
            # pay a round trip to be told so.
            raise UnsupportedLanguage(
                f"{self.caps.name} does not serve {req.language}; "
                f"serves {sorted(self.caps.languages)}"
            )
        if req.voice_id.startswith("clone:") and not self.caps.supports_cloning:
            raise UnsupportedCapability(f"{self.caps.name} is a fixed-voice model")

        try:
            async with websockets.connect(
                self._url, open_timeout=self._timeout, max_size=None
            ) as ws:
                self._sockets[req.request_id] = ws
                await ws.send(req.model_dump_json())
                seq = 0
                async for msg in ws:
                    if isinstance(msg, bytes):
                        yield AudioChunk(data=msg, seq=seq)
                        seq += 1
                        continue
                    if '"kind"' in msg:
                        err = TTSError.model_validate_json(msg)
                        raise _KIND_TO_EXC[err.kind](f"{self.caps.name}: {err.error}")
                    yield StreamDone(trailer=TTSTrailer.model_validate_json(msg))
                    return
        except (OSError, websockets.WebSocketException) as e:
            raise ProviderUnavailable(f"{self.caps.name}: {e}") from e
        finally:
            self._sockets.pop(req.request_id, None)

    async def cancel(self, request_id: str) -> None:
        ws = self._sockets.get(request_id)
        if ws is not None:
            await ws.send(TTSCancel(cancel=request_id).model_dump_json())

    async def health(self) -> ProviderHealth:
        url = self._base.replace("ws://", "http://").replace("wss://", "https://")
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                r = await c.get(f"{url}/health")
                return ProviderHealth(name=self.caps.name, healthy=r.status_code == 200)
        except httpx.HTTPError as e:
            return ProviderHealth(name=self.caps.name, healthy=False, detail=str(e))
