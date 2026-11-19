"""Adapts a gotiny STTBackend onto Pipecat's SegmentedSTTService.

SegmentedSTTService is the right base: it buffers audio and triggers on VAD
boundaries, which is exactly the VAD-segmented design our STT wire protocol
assumes -- IndicConformer ships as an offline checkpoint with no cache-aware
streaming decoder, so pretending to stream would be a lie in ProviderCaps.

Verified against pipecat-ai 1.7.0: module path, ``run_stt(audio)`` signature,
and TranscriptionFrame's field set.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from pipecat.frames.frames import ErrorFrame, Frame, TranscriptionFrame
from pipecat.services.settings import STTSettings
from pipecat.services.stt_service import SegmentedSTTService

from gotiny.core.errors import ProviderError
from gotiny.core.ids import new_request_id
from gotiny.core.types import Language
from gotiny.providers.base import STTBackend
from gotiny.providers.wire import STTRequest, STTResponse


class GotinySTTService(SegmentedSTTService):
    def __init__(
        self,
        *,
        backend: STTBackend,
        language: Language,
        sample_rate: int | None = None,
        **kwargs: object,
    ) -> None:
        # See the TTS bridge: Settings must be fully initialized in 1.7, and
        # None means "this service does not use that field".
        super().__init__(
            sample_rate=sample_rate,
            settings=STTSettings(model=None, language=None),
            **kwargs,  # type: ignore[arg-type]
        )
        self._backend = backend
        self._language = language
        self._sample_rate_hint = sample_rate or 16_000
        self.last_response: STTResponse | None = None

    @property
    def _rate(self) -> int:
        """``self.sample_rate`` is 0 until the pipeline's StartFrame arrives.

        In a live pipeline start() always runs first, but reading it unguarded
        makes the service unusable outside one -- including in tests -- and a
        sample_rate of 0 propagates silently into audio-duration maths.
        """
        return self.sample_rate or self._sample_rate_hint

    def can_generate_metrics(self) -> bool:
        return True

    async def run_stt(self, audio: bytes) -> AsyncGenerator[Frame | None, None]:
        req = STTRequest(
            request_id=new_request_id(),
            language=self._language,
            sample_rate=self._rate,
        )
        await self.start_ttfb_metrics()
        try:
            res = await self._backend.transcribe(audio, req)
        except ProviderError as e:
            yield ErrorFrame(error=f"stt:{self._backend.caps.name}: {e}")
            return
        await self.stop_ttfb_metrics()
        self.last_response = res

        if not res.text.strip():
            return
        # TranscriptionFrame is a dataclass whose first fields are inherited
        # (id, name, pts, ...), so these MUST be keyword arguments. Passing them
        # positionally silently populates the wrong fields.
        yield TranscriptionFrame(
            text=res.text,
            user_id="",
            timestamp=datetime.now(UTC).isoformat(),
            language=None,  # TODO(step 3): map gotiny Language -> pipecat Language
        )
