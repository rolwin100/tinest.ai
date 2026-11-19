"""Text in, audio frames out -- the whole of what a synthesis request does.

The server owns three things here so that no backend has to: sentence
segmentation (kokoro-onnx and IndicF5 both synthesise whole strings), resampling
to the requested rate, and cancellation between segments.

Everything below is driven by its arguments -- no FastAPI app, no global state --
so the pipeline can be exercised against a fake backend without a socket.
"""

import asyncio
import time

from fastapi import WebSocket

from gotiny.core.errors import ProviderUnavailable, UnsupportedCapability, UnsupportedLanguage
from gotiny.core.logging import get_logger
from gotiny.providers.wire import TTSError, TTSRequest, TTSTrailer
from gotiny.tts.services.routing import VoiceRouter
from gotiny.audio import duration_ms, resample_pcm
from gotiny.tts.util.segment import split_sentences
from gotiny.tts.util.speakable import speakable

log = get_logger("gotiny.tts.synthesis")


async def synthesise(
    ws: WebSocket, router: VoiceRouter, req: TTSRequest, cancelled: asyncio.Event
) -> None:
    """Stream one request: binary PCM frames, then exactly one JSON trailer.

    A request that cannot be served gets a ``TTSError`` frame instead of a
    trailer, and no audio.
    """
    try:
        backend, spec = router.resolve(req.voice_id)
    except KeyError as e:
        await _fail(ws, req, "unknown_voice", str(e))
        return
    except ProviderUnavailable as e:
        await _fail(ws, req, "internal", str(e))
        return

    if not backend.caps.supports(req.language):
        await _fail(ws, req, "unsupported_language", f"{backend.caps.name}: {req.language}")
        return
    if req.voice_id.startswith("clone:") and not backend.caps.supports_cloning:
        await _fail(ws, req, "unsupported_capability", f"{backend.caps.name} is fixed-voice")
        return

    # Clean before segmenting: a direction removed after the split would leave
    # an empty segment, and one spanning a sentence boundary would only be half
    # removed.
    spoken = speakable(req.text)
    if spoken != req.text:
        log.info("text_cleaned", request_id=req.request_id, before=req.text, after=spoken)
    segments = split_sentences(spoken)
    t0 = time.perf_counter()
    ttfb_ms: float | None = None
    audio_ms = 0.0
    emitted = 0

    for segment in segments:
        # Cancellation is checked BETWEEN segments: "drop the remaining
        # sentences", not "stop mid-sample" (ADR 0004).
        if cancelled.is_set():
            log.info("cancelled", request_id=req.request_id, after_segments=emitted)
            break
        try:
            pcm = await backend.synth(
                segment, voice=spec.voice, language=req.language, speed=req.speed
            )
        except UnsupportedLanguage as e:
            await _fail(ws, req, "unsupported_language", str(e))
            return
        except UnsupportedCapability as e:
            await _fail(ws, req, "unsupported_capability", str(e))
            return
        except Exception as e:  # noqa: BLE001 - a model blowing up must not hang the caller
            log.exception("synth_failed", request_id=req.request_id)
            await _fail(ws, req, "internal", f"{type(e).__name__}: {e}")
            return

        if not pcm:
            continue
        pcm = resample_pcm(pcm, backend.native_sample_rate, req.sample_rate)
        if ttfb_ms is None:
            ttfb_ms = (time.perf_counter() - t0) * 1_000
        audio_ms += duration_ms(pcm, req.sample_rate)
        emitted += 1
        await ws.send_bytes(pcm)

    trailer = TTSTrailer(
        request_id=req.request_id,
        ttfb_ms=ttfb_ms if ttfb_ms is not None else (time.perf_counter() - t0) * 1_000,
        audio_ms=audio_ms,
        chars=len(spoken),
        provider=backend.caps.name,
    )
    await ws.send_text(trailer.model_dump_json())
    log.info(
        "synthesised",
        request_id=req.request_id,
        provider=backend.caps.name,
        segments=f"{emitted}/{len(segments)}",
        ttfb_ms=round(trailer.ttfb_ms),
        audio_ms=round(audio_ms),
    )


async def _fail(ws: WebSocket, req: TTSRequest, kind: str, detail: str) -> None:
    log.warning("tts_error", request_id=req.request_id, kind=kind, detail=detail)
    await ws.send_text(
        TTSError(request_id=req.request_id, error=detail, kind=kind).model_dump_json()  # type: ignore[arg-type]
    )
