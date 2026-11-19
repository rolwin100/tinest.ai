"""voice_id -> backend instance.

Trivial today (one backend). It exists now because the two-model fleet is a
planned, not hypothetical, outcome: preset voices on a small non-autoregressive
model, cloned voices on a reference-conditioned one (ADR 0005). Routing by voice
rather than by request field is what keeps that invisible to callers.
"""

from gotiny.core.errors import ProviderUnavailable
from gotiny.tts.backends.base import SynthBackend
from gotiny.tts.repositories.voices import VoiceRegistry, VoiceSpec


class VoiceRouter:
    """Backends arrive already loaded -- see ``backends/loader.py``."""

    def __init__(self, backends: dict[str, SynthBackend], voices: VoiceRegistry) -> None:
        self._backends = backends
        self._voices = voices

    def resolve(self, voice_id: str) -> tuple[SynthBackend, VoiceSpec]:
        # Cheap: one stat() per request, a parse only when the file changed.
        # Buys an edit-listen loop on instruct strings with no weight reload.
        self._voices.maybe_reload()
        spec = self._voices.get(voice_id)
        backend = self._backends.get(spec.backend)
        if backend is None:
            raise ProviderUnavailable(
                f"voice {voice_id!r} needs backend {spec.backend!r}, which is not loaded"
            )
        return backend, spec

    @property
    def voices(self) -> VoiceRegistry:
        return self._voices

    def backend_caps(self) -> list[dict]:
        return [b.caps.model_dump(mode="json") for b in self._backends.values()]
