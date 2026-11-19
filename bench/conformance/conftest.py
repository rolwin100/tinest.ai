"""Every provider is tested by the same suite.

Register a new backend by appending a factory below. A factory that needs a
running server should return ``None`` when it is unreachable, so the suite skips
instead of failing red on a laptop with nothing started.
"""

from collections.abc import Callable

import pytest

from gotiny.core.settings import settings

from conformance.fakes import FakeFrameTTS, FakeSTT, FakeUtteranceTTS


def live_tts_server() -> object | None:
    """The real TTS server, if it is running.

    Returns None when unreachable so `just conformance` stays green on a laptop
    with nothing started -- but when the server IS up, the real model is held to
    exactly the same contract as the fakes. That is the whole point of the seam.
    """
    from gotiny.providers.tts.http import HTTPTTSBackend

    try:
        return HTTPTTSBackend.discover(settings.tts_url)
    except Exception:
        return None


def live_stt_server() -> object | None:
    """The real STT server, if it is running. Same contract as the fakes."""
    from gotiny.providers.stt.http import HTTPSTTBackend

    try:
        return HTTPSTTBackend.discover(settings.stt_url)
    except Exception:
        return None

# ── add real providers here as they arrive (step 3: kokoro, week 3: indicf5) ──
TTS_BACKENDS: list[Callable[[], object | None]] = [
    FakeFrameTTS,
    FakeUtteranceTTS,
    live_tts_server,
]

STT_BACKENDS: list[Callable[[], object | None]] = [
    FakeSTT,
    live_stt_server,
]


def _build(factory: Callable[[], object | None]) -> object:
    try:
        backend = factory()
    except Exception as e:  # noqa: BLE001 - unreachable server is a skip, not a failure
        pytest.skip(f"{factory.__name__} unavailable: {e}")
    if backend is None:
        pytest.skip(f"{factory.__name__} unavailable")
    return backend


@pytest.fixture(params=TTS_BACKENDS, ids=lambda f: f.__name__)
def tts(request: pytest.FixtureRequest) -> object:
    return _build(request.param)


@pytest.fixture(params=STT_BACKENDS, ids=lambda f: f.__name__)
def stt(request: pytest.FixtureRequest) -> object:
    return _build(request.param)
