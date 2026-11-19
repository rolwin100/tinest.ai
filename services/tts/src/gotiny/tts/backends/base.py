"""Server-side backend interface.

Note this is *not* the same thing as ``gotiny.providers.base.TTSBackend``.
That one is the client's view across the wire. This one is what a set of model
weights must implement inside the server. Keeping them separate is what lets the
server own segmentation, resampling and cancellation once, for every model.
"""

from typing import Protocol

from gotiny.core.types import Language
from gotiny.providers.caps import ProviderCaps


class SynthBackend(Protocol):
    caps: ProviderCaps
    native_sample_rate: int

    async def load(self) -> None:
        """Load weights. Called once at startup, never on the request path."""
        ...

    async def synth(self, segment: str, *, voice: str, language: Language, speed: float) -> bytes:
        """Synthesise ONE segment. Returns PCM s16le mono at native_sample_rate."""
        ...
