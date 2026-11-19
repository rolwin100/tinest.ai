"""Adapts a gotiny TTSBackend onto Pipecat's TTSService.

Deliberately thin. We subclass Pipecat rather than reimplementing frame
semantics because the base class already gives us interruption handling and
TTFB/usage metrics -- the exact spans our latency budget is measured against.
Rebuilding that would be work spent in order to lose instrumentation.

Verified against pipecat-ai 1.7.0: module path, ``run_tts(text, context_id)``
signature, and the metrics method names. ``push_start_frame`` and
``push_stop_frames`` both default to False, so the subclass yields the
Started/Stopped frames itself.
"""

from collections.abc import AsyncGenerator

from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.services.settings import TTSSettings
from pipecat.services.tts_service import TTSService

from gotiny.core.errors import Cancelled, ProviderError
from gotiny.core.ids import new_request_id
from gotiny.core.types import Language
from gotiny.providers.base import TTSBackend
from gotiny.providers.wire import AudioChunk, StreamDone, TTSRequest, TTSTrailer


class GotinyTTSService(TTSService):
    """One service, any backend. Which model answers is decided server-side."""

    def __init__(
        self,
        *,
        backend: TTSBackend,
        voice_id: str,
        language: Language,
        sample_rate: int | None = None,
        speed: float = 1.0,
        **kwargs: object,
    ) -> None:
        # Pipecat 1.7 validates that every Settings field is initialized and
        # logs an error for any left NOT_GIVEN. `model` is None because the model
        # is chosen server-side by voice_id, not named by the client.
        super().__init__(
            sample_rate=sample_rate,
            settings=TTSSettings(model=None, voice=voice_id, language=None),
            **kwargs,  # type: ignore[arg-type]
        )
        self._backend = backend
        self._voice_id = voice_id
        self._language = language
        self._active: str | None = None
        self._sample_rate_hint = sample_rate or 24_000
        self._speed = speed
        self.last_trailer: TTSTrailer | None = None

    @property
    def _rate(self) -> int:
        """Guard: sample_rate is resolved from the StartFrame at pipeline start."""
        return self.sample_rate or self._sample_rate_hint

    def can_generate_metrics(self) -> bool:
        return True

    async def run_tts(self, text: str, context_id: str) -> AsyncGenerator[Frame | None, None]:
        req = TTSRequest(
            request_id=new_request_id(),
            text=text,
            voice_id=self._voice_id,
            language=self._language,
            sample_rate=self._rate,
            speed=self._speed,
        )
        self._active = req.request_id
        await self.start_ttfb_metrics()
        yield TTSStartedFrame()

        # NB: no `yield` inside a finally block. On barge-in Pipecat closes this
        # generator, and yielding during GeneratorExit raises
        # "async generator ignored GeneratorExit".
        try:
            async for event in self._backend.stream(req):
                if isinstance(event, AudioChunk):
                    await self.stop_ttfb_metrics()
                    yield TTSAudioRawFrame(
                        audio=event.data,
                        sample_rate=self._rate,
                        num_channels=1,
                    )
                elif isinstance(event, StreamDone):
                    # The trailer carries ttfb_ms / audio_ms / chars, which the
                    # agent writes onto the `turn` row.
                    self.last_trailer = event.trailer
                    await self.start_tts_usage_metrics(text)
        except Cancelled:
            pass  # barge-in is correct behaviour, not an error
        except ProviderError as e:
            yield ErrorFrame(error=f"tts:{self._backend.caps.name}: {e}")

        self._active = None
        yield TTSStoppedFrame()

    async def _handle_interruption(self, *args: object, **kwargs: object) -> None:
        """Tell the model server to stop. Contract: drop remaining sentences."""
        if self._active:
            await self._backend.cancel(self._active)
            self._active = None
        await super()._handle_interruption(*args, **kwargs)  # type: ignore[misc]
