"""Whisper via faster-whisper (CTranslate2).

Chosen for step 1.6 because it runs on CPU with int8 quantisation, handles
Hinglish tolerably out of the box, and needs no GPU on the Mac. IndicConformer
is the week-3 challenger; whichever wins the bench on our own recorded set
becomes the cloud deployment.

Honest caps: ``streaming=False``. Whisper is an encoder-decoder over a 30 s
window -- it cannot emit partial hypotheses as audio arrives. Our design is
VAD-segmented pseudo-streaming: the transport detects an endpoint, sends the
segment, gets a final transcript. Claiming ``streaming=True`` here would be a
lie the latency budget then gets built on.
"""

import asyncio
import math
import os

from gotiny.audio import pcm_to_float32
from gotiny.core.errors import ProviderUnavailable, UnsupportedLanguage
from gotiny.core.logging import get_logger
from gotiny.core.types import Language
from gotiny.providers.caps import ProviderCaps
from gotiny.stt.backends.base import Transcript

log = get_logger("gotiny.stt.whisper")

# Whisper's own codes. HINGLISH maps to "hi": Whisper has no code-switching
# code, and forcing "hi" keeps the output script consistent rather than letting
# the decoder flip mid-utterance.
#
# OPEN QUESTION for week 3's bench: for Hinglish, is forced "hi" better than
# auto-detect, or than `multilingual=True`? That is a measurement, not an
# opinion, and it needs the 300-utterance set to answer. Left configurable so
# the bench can sweep it.
_LANG = {
    Language.HINDI: "hi",
    Language.HINGLISH: "hi",
    Language.ENGLISH_IN: "en",
    Language.ENGLISH_US: "en",
    Language.TAMIL: "ta",
    Language.TELUGU: "te",
    Language.MARATHI: "mr",
    Language.BENGALI: "bn",
    Language.GUJARATI: "gu",
    Language.KANNADA: "kn",
    Language.MALAYALAM: "ml",
    Language.PUNJABI: "pa",
}


class FasterWhisperBackend:
    native_sample_rate = 16_000

    def __init__(
        self,
        model_size: str | None = None,
        compute_type: str | None = None,
        multilingual: bool | None = None,
    ) -> None:
        self._model = None
        self._size = model_size or os.getenv("GOTINY_WHISPER_MODEL", "small")
        self._compute = compute_type or os.getenv("GOTINY_WHISPER_COMPUTE", "int8")
        self._multilingual = (
            multilingual
            if multilingual is not None
            else os.getenv("GOTINY_WHISPER_MULTILINGUAL", "0") == "1"
        )
        self.caps = ProviderCaps(
            name=f"faster-whisper-{self._size}@1.0",
            modality="stt",
            languages=frozenset(_LANG),
            sample_rates=frozenset({8_000, 16_000, 24_000}),
            streaming=False,
            chunk_granularity="utterance",
        )

    async def load(self) -> None:
        try:
            from faster_whisper import WhisperModel
        except ModuleNotFoundError as e:
            raise ProviderUnavailable(
                "faster-whisper not installed; run: uv sync --all-packages --extra whisper"
            ) from e
        self._model = await asyncio.to_thread(
            WhisperModel, self._size, device="cpu", compute_type=self._compute
        )
        log.info("whisper_loaded", model=self._size, compute=self._compute)

    async def transcribe(self, pcm: bytes, *, language: Language) -> Transcript:
        if self._model is None:
            raise ProviderUnavailable("whisper backend not loaded")
        code = _LANG.get(language)
        if code is None:
            raise UnsupportedLanguage(f"whisper has no code for {language}")

        samples = pcm_to_float32(pcm)

        def _run() -> tuple[list, object]:
            # `transcribe` returns a LAZY generator: consuming it is what does
            # the work. It must be drained inside this thread, or the decode
            # runs on the event loop and blocks every other call on the box.
            segments, info = self._model.transcribe(  # type: ignore[union-attr]
                samples,
                language=code,
                beam_size=1,  # greedy: latency beats the last 1% of WER here
                vad_filter=False,  # the transport already segmented on VAD
                condition_on_previous_text=False,  # each utterance is independent
                multilingual=self._multilingual,
            )
            return list(segments), info

        segments, info = await asyncio.to_thread(_run)
        text = "".join(s.text for s in segments).strip()
        confidence = (
            math.exp(sum(s.avg_logprob for s in segments) / len(segments)) if segments else None
        )
        return Transcript(
            text=text,
            detected_language=getattr(info, "language", None),
            confidence=confidence,
        )
