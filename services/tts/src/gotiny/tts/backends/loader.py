"""Which backends this process can actually serve.

Two things decide that, and both belong next to the backends rather than in the
FastAPI module: whether a model's extra is installed at all, and whether its
weights load.

Backends come back already loaded. Loading is deliberately not a method on
``VoiceRouter`` -- picking a model for a voice and bringing a model up are
different concerns, and only one of them is a lifecycle.

The distinction that matters, learned by breaking it (ADR 0005): a backend whose
dependencies are absent means *this box does not serve that model* -- skip it and
carry on. Any other failure means a backend that should work does not, and that
should be loud. An earlier version caught only ImportError at the import
statement, but a missing extra actually surfaces later, from ``load()``, as
ProviderUnavailable -- so adding one optional backend took the entire server
down for anyone who had not installed it.
"""

from collections.abc import Callable

from gotiny.core.errors import ProviderUnavailable
from gotiny.core.logging import get_logger
from gotiny.tts.backends.base import SynthBackend

log = get_logger("gotiny.tts.backends")


def _candidates() -> list[tuple[str, Callable[[], SynthBackend]]]:
    """Imported lazily: a missing extra must not break the import of this module."""
    out: list[tuple[str, Callable[[], SynthBackend]]] = []
    try:
        from gotiny.tts.backends.kokoro import KokoroBackend
    except ImportError:  # pragma: no cover - depends on installed extras
        log.warning("backend_module_unavailable", backend="kokoro")
    else:
        out.append(("kokoro", KokoroBackend))
    try:
        from gotiny.tts.backends.qwen3_tts import Qwen3TTSBackend
    except ImportError:  # pragma: no cover
        log.warning("backend_module_unavailable", backend="qwen3-tts")
    else:
        out.append(("qwen3-tts", Qwen3TTSBackend))
    return out


async def load_backends() -> dict[str, SynthBackend]:
    """Construct and load every backend this box can serve.

    Keyed by ``caps.name`` -- the same ``name@semver`` that ``voices.yaml`` names
    in its ``backend`` field, which is what lets the two tables join.
    """
    backends: dict[str, SynthBackend] = {}

    for label, factory in _candidates():
        backend = factory()
        try:
            await backend.load()
        except ProviderUnavailable as e:
            # Dependencies or weights absent: this box does not serve this model.
            log.warning("backend_skipped", backend=label, reason=str(e))
            continue
        backends[backend.caps.name] = backend
        log.info("backend_ready", backend=backend.caps.name)

    if not backends:
        raise RuntimeError(
            "no TTS backend could be loaded; install one, e.g. "
            "`uv sync --all-packages --extra kokoro`"
        )
    return backends
