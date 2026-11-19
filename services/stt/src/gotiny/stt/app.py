"""STT model server -- speaks wire protocol v1.

Composition root, and nothing else. Endpoints live in ``api/``, the work behind
them in ``services/``, the model adapters in ``backends/``.

No ``repositories/`` layer: unlike TTS there is no catalogue to resolve -- a
request names a language, not a voice. No ``services/stream.py`` either, because
this endpoint is request/response. Whisper is an encoder-decoder over a 30 s
window and cannot emit partial hypotheses, so the design is VAD-segmented
pseudo-streaming rather than a socket.
"""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from gotiny.core.logging import configure, get_logger
from gotiny.core.settings import settings
from gotiny.stt.api import caps, health, transcribe
from gotiny.stt.backends.loader import load_backends
from gotiny.stt.services.routing import LanguageRouter

log = get_logger("gotiny.stt")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure(settings.log_level, json_output=settings.env != "local")
    t0 = time.perf_counter()
    backends = await load_backends()
    log.info("backends_loaded", ms=round((time.perf_counter() - t0) * 1000))
    app.state.router = LanguageRouter(backends)
    yield


app = FastAPI(title="gotiny-stt", lifespan=lifespan)

app.include_router(health.router)
app.include_router(caps.router)
app.include_router(transcribe.router)
