"""Server-side backend interface.

Not the same thing as ``gotiny.providers.base.STTBackend`` -- that is the
client's view across the wire. This is what a set of weights must implement
inside the server, so the server can own resampling and response assembly once
for every model.
"""

from typing import Protocol

from gotiny.core.types import Language
from gotiny.providers.caps import ProviderCaps


class Transcript:
    """What a backend returns. Deliberately not the wire type.

    ``detected_language`` and ``confidence`` are separate from ``text`` because
    week 3's benchmark scores them separately, and because a low-confidence
    transcript on a noisy line is a different product problem from a wrong one.
    """

    __slots__ = ("confidence", "detected_language", "text")

    def __init__(
        self, text: str, detected_language: str | None = None, confidence: float | None = None
    ) -> None:
        self.text = text
        self.detected_language = detected_language
        self.confidence = confidence


class TranscribeBackend(Protocol):
    caps: ProviderCaps
    native_sample_rate: int

    async def load(self) -> None:
        """Load weights. Called once at startup, never on the request path."""
        ...

    async def transcribe(self, pcm: bytes, *, language: Language) -> Transcript:
        """Transcribe one VAD-segmented utterance of PCM s16le at native_sample_rate."""
        ...
