"""language -> backend instance.

The STT mirror of the TTS router, and it exists for the same reason: week 3 puts
IndicConformer alongside Whisper, and which one answers should be a property of
the request's language, not an if-statement in the endpoint.

Today the rule is "first loaded backend that claims the language" -- correct for
one backend, and a placeholder for the bench-off that picks between two.
"""

from gotiny.core.errors import UnsupportedLanguage
from gotiny.core.types import Language
from gotiny.stt.backends.base import TranscribeBackend


class LanguageRouter:
    """Backends arrive already loaded -- see ``backends/loader.py``."""

    def __init__(self, backends: dict[str, TranscribeBackend]) -> None:
        self._backends = backends

    def resolve(self, language: Language) -> TranscribeBackend:
        for backend in self._backends.values():
            if backend.caps.supports(language):
                return backend
        raise UnsupportedLanguage(
            f"no loaded backend serves {language}; loaded: {sorted(self._backends)}"
        )

    def backend_caps(self) -> list[dict]:
        return [b.caps.model_dump(mode="json") for b in self._backends.values()]

    @property
    def names(self) -> list[str]:
        return sorted(self._backends)
