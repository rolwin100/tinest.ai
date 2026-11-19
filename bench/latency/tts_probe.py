"""Measure TTS first-byte latency against a running server, and write a wav.

This fills in the row the architecture plan deliberately left as "TBD -- measure
first". For a whole-utterance model, TTFB is first-*segment* synthesis time, so
the number is only meaningful once the server is doing the segmentation.

    just say "नमस्ते।"
"""

import argparse
import asyncio
import time
import wave
from pathlib import Path

from gotiny.core.errors import GotinyError
from gotiny.core.ids import new_request_id
from gotiny.core.settings import settings
from gotiny.core.types import Language
from gotiny.providers.tts.http import HTTPTTSBackend
from gotiny.providers.wire import AudioChunk, StreamDone, TTSRequest


async def probe(
    text: str, voice: str, language: Language, rate: int, out: Path, speed: float = 1.0
) -> None:
    backend = HTTPTTSBackend.discover(settings.tts_url)
    req = TTSRequest(
        request_id=new_request_id(),
        text=text,
        voice_id=voice,
        language=language,
        sample_rate=rate,
        speed=speed,
    )

    t0 = time.perf_counter()
    marks: list[float] = []
    pcm = bytearray()
    trailer = None
    async for event in backend.stream(req):
        if isinstance(event, AudioChunk):
            marks.append((time.perf_counter() - t0) * 1_000)
            pcm += event.data
        elif isinstance(event, StreamDone):
            trailer = event.trailer
    wall = (time.perf_counter() - t0) * 1_000

    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(pcm))

    audio_ms = trailer.audio_ms if trailer else 0.0
    print(f"provider     {trailer.provider if trailer else '?'}")
    print(f"speed        {speed}")
    print(f"segments     {len(marks)}")
    if marks:
        print(f"TTFB         {marks[0]:.0f} ms   <-- what the caller actually waits for")
    print(f"wall         {wall:.0f} ms")
    print(f"audio        {audio_ms:.0f} ms")
    # RTF > ~0.9 means synthesis cannot keep ahead of playback and audio stutters.
    print(f"RTF          {wall / audio_ms:.2f}" if audio_ms else "RTF          n/a")
    if len(marks) > 1:
        print(f"segment at   {[round(m) for m in marks]} ms")
        print(f"segmentation saved {wall - marks[0]:.0f} ms of TTFB")
    print(f"wrote        {out}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--text", default="नमस्ते। मैं आपकी मदद कर सकती हूँ। कृपया अपना नाम बताइए।")
    p.add_argument("--voice", default="hi-female-01")
    p.add_argument("--language", default=Language.HINDI.value)
    p.add_argument("--rate", type=int, default=24_000)
    # Auditioning a voice means hearing its pace too, and pace is a per-request
    # field -- so it belongs here, not only in the persona.
    p.add_argument("--speed", type=float, default=1.0)
    p.add_argument("--out", type=Path, default=Path("out.wav"))
    a = p.parse_args()
    try:
        asyncio.run(probe(a.text, a.voice, Language(a.language), a.rate, a.out, a.speed))
    except GotinyError as e:
        raise SystemExit(f"error: {e}") from None


if __name__ == "__main__":
    main()
