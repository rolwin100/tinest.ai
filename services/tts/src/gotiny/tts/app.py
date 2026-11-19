"""TTS model server -- speaks wire protocol v1.

Composition root, and nothing else. Endpoints live in ``api/``, the work behind
them in ``services/``, the model adapters in ``backends/``.
"""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from gotiny.core.logging import configure, get_logger
from gotiny.core.settings import settings
from gotiny.tts.api import caps, health, stream
from gotiny.tts.backends.loader import load_backends
from gotiny.tts.repositories.voices import VoiceRegistry
from gotiny.tts.services.routing import VoiceRouter

log = get_logger("gotiny.tts")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure(settings.log_level, json_output=settings.env != "local")
    t0 = time.perf_counter()
    # Weights load at startup, never on the request path. A cold model on the
    # first call would eat the entire latency budget.
    backends = await load_backends()
    log.info("backends_loaded", ms=round((time.perf_counter() - t0) * 1000))
    app.state.router = VoiceRouter(backends, VoiceRegistry.load())
    yield


app = FastAPI(title="gotiny-tts", lifespan=lifespan)

app.include_router(health.router)
app.include_router(caps.router)
app.include_router(stream.router)
