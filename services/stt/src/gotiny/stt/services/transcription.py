"""Audio in, transcript out -- the whole of what a transcription request does.

The server owns resampling and response assembly so that no backend has to.

Driven entirely by its arguments -- no FastAPI, no global state -- so the
pipeline can be exercised against a stub backend with no HTTP at all. Week 2's
latency harness will want exactly that.
"""

import time

from gotiny.audio import duration_ms, resample_pcm
from gotiny.core.logging import get_logger
from gotiny.providers.wire import STTRequest, STTResponse
from gotiny.stt.services.routing import LanguageRouter

log = get_logger("gotiny.stt.transcription")


async def transcribe(pcm: bytes, req: STTRequest, router: LanguageRouter) -> STTResponse:
    backend = router.resolve(req.language)

    # Reported at the WIRE rate, not the model rate: audio_ms feeds per-minute
    # COGS, and that must reflect what the caller actually sent.
    audio_ms = duration_ms(pcm, req.sample_rate)

    # Telephony arrives at 8 kHz; Whisper wants 16 kHz. Upsampling adds no
    # information, but feeding a model the rate it was trained on is not optional.
    audio = resample_pcm(pcm, req.sample_rate, backend.native_sample_rate)

    t0 = time.perf_counter()
    result = await backend.transcribe(audio, language=req.language)
    elapsed = (time.perf_counter() - t0) * 1_000

    log.info(
        "transcribed",
        request_id=req.request_id,
        provider=backend.caps.name,
        audio_ms=round(audio_ms),
        elapsed_ms=round(elapsed),
        # RTF > 1 means we cannot transcribe as fast as people speak.
        rtf=round(elapsed / audio_ms, 2) if audio_ms else None,
        chars=len(result.text),
    )
    return STTResponse(
        request_id=req.request_id,
        text=result.text,
        language=req.language,
        audio_ms=audio_ms,
        provider=backend.caps.name,
        confidence=result.confidence,
    )
