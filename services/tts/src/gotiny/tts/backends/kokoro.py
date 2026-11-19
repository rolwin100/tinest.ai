"""Kokoro-82M via kokoro-onnx.

Chosen for step 1.5 because it is 82M parameters, runs on CPU with no GPU and no
torch, is Apache-2.0, and was trained for ~$1k of compute -- which is the Phase 2
budget, so living inside its constraints is research.

Honest caps: ``streaming=False``, ``chunk_granularity="utterance"``. kokoro-onnx
synthesises a whole input string in one shot; the sentence-level streaming the
wire protocol advertises is produced by the *server* (see segment.py), not here.

Its four Hindi voices are graded C on 10-100 minutes of data each. This backend
proves the pipe; IndicF5 in week 3 is the real Indic voice.
"""

import asyncio
import os
from pathlib import Path

import numpy as np

from gotiny.core.errors import ProviderUnavailable, UnsupportedLanguage
from gotiny.core.types import Language
from gotiny.providers.caps import ProviderCaps

CACHE = Path(os.path.expanduser(os.getenv("GOTINY_KOKORO_CACHE", "~/.cache/gotiny/kokoro")))
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

# Kokoro's own language codes. Note en-IN is absent: Kokoro has no Indian-English
# voice, so we do not claim one. Mapping it to en-us would be a quiet lie.
_LANG = {
    Language.HINDI: "hi",
    Language.HINGLISH: "hi",
    Language.ENGLISH_US: "en-us",
}


class KokoroBackend:
    native_sample_rate = 24_000

    caps = ProviderCaps(
        name="kokoro-onnx@1.0",
        modality="tts",
        languages=frozenset(_LANG),
        sample_rates=frozenset({8_000, 16_000, 24_000}),
        streaming=False,
        supports_cloning=False,
        chunk_granularity="utterance",
    )

    def __init__(self) -> None:
        self._kokoro = None

    async def load(self) -> None:
        try:
            from kokoro_onnx import Kokoro
        except ModuleNotFoundError as e:
            raise ProviderUnavailable(
                "kokoro-onnx not installed; run: uv sync --all-packages --extra kokoro"
            ) from e

        model, voices = CACHE / "kokoro-v1.0.onnx", CACHE / "voices-v1.0.bin"
        _ensure(model, MODEL_URL)
        _ensure(voices, VOICES_URL)
        # to_thread: loading weights on the event loop blocks for seconds.
        self._kokoro = await asyncio.to_thread(Kokoro, str(model), str(voices))

    async def synth(self, segment: str, *, voice: str, language: Language, speed: float) -> bytes:
        if self._kokoro is None:
            raise ProviderUnavailable("kokoro backend not loaded")
        lang = _LANG.get(language)
        if lang is None:
            raise UnsupportedLanguage(f"kokoro-onnx has no voice for {language}")

        chunks: list[np.ndarray] = []
        async for samples, _rate in self._kokoro.create_stream(
            segment, voice=voice, lang=lang, speed=speed
        ):
            chunks.append(np.asarray(samples, dtype=np.float32))
        if not chunks:
            return b""
        audio = np.concatenate(chunks)
        return (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()


def _ensure(path: Path, url: str) -> None:
    """Download weights once, at startup. Never on the request path."""
    if path.exists():
        return
    import urllib.request

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)  # noqa: S310 - pinned release URL
    tmp.rename(path)
