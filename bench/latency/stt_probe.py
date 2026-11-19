"""Transcribe a wav against a running STT server and report latency.

    just hear out.wav

RTF is the number to watch: above 1.0 the box cannot transcribe as fast as
people speak, which means queueing under any concurrency at all.
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
from gotiny.providers.stt.http import HTTPSTTBackend
from gotiny.providers.wire import STTRequest


def read_wav(path: Path) -> tuple[bytes, int]:
    with wave.open(str(path), "rb") as w:
        if w.getsampwidth() != 2 or w.getnchannels() != 1:
            raise SystemExit(f"{path}: need 16-bit mono PCM")
        return w.readframes(w.getnframes()), w.getframerate()


async def probe(path: Path, language: Language) -> None:
    pcm, rate = read_wav(path)
    backend = HTTPSTTBackend.discover(settings.stt_url)
    req = STTRequest(request_id=new_request_id(), language=language, sample_rate=rate)

    t0 = time.perf_counter()
    res = await backend.transcribe(pcm, req)
    elapsed = (time.perf_counter() - t0) * 1_000

    print(f"provider     {res.provider}")
    print(f"input        {path.name} @ {rate} Hz, {res.audio_ms:.0f} ms")
    print(f"elapsed      {elapsed:.0f} ms")
    print(f"RTF          {elapsed / res.audio_ms:.2f}" if res.audio_ms else "RTF          n/a")
    if res.confidence is not None:
        print(f"confidence   {res.confidence:.2f}")
    print(f"text         {res.text!r}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("wav", type=Path)
    p.add_argument("--language", default=Language.HINGLISH.value)
    a = p.parse_args()
    try:
        asyncio.run(probe(a.wav, Language(a.language)))
    except GotinyError as e:
        raise SystemExit(f"error: {e}") from None


if __name__ == "__main__":
    main()
