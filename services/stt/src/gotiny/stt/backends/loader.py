"""Which backends this process can actually serve.

Same shape as the TTS loader, same reasoning: whether a model's extra is
installed and whether its weights load are decisions that belong next to the
backends, not in the FastAPI module. Backends come back already loaded.
"""

from gotiny.core.logging import get_logger
from gotiny.stt.backends.base import TranscribeBackend

log = get_logger("gotiny.stt.backends")


async def load_backends() -> dict[str, TranscribeBackend]:
    """Construct and load every backend whose deps are installed.

    Keyed by ``caps.name`` -- the ``name@semver`` written onto every ``turn``
    row. A missing extra is tolerated; a backend that IS installed but fails to
    load takes startup down, which is right while there is one model.
    """
    backends: dict[str, TranscribeBackend] = {}

    try:
        from gotiny.stt.backends.faster_whisper import FasterWhisperBackend
    except ImportError:  # pragma: no cover - depends on installed extras
        log.warning("faster-whisper backend unavailable")
    else:
        backend = FasterWhisperBackend()
        await backend.load()
        backends[backend.caps.name] = backend

    return backends
