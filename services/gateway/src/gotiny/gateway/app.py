"""The gateway -- the only deployable process in the media plane.

Composition root. It owns three things a Pipecat example does not: signaling
(``api/offer.py``), how many calls this box will take (``services/sessions.py``),
and what happens on SIGTERM (``services/lifecycle.py``).

The agent is a *library* here, not a service: ``packages/gotiny-agent`` is
imported and hosted as one asyncio task per call. No service imports another
service; when process-per-call is justified by measurement, ``services/agent``
becomes a thin entrypoint around the same package.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pipecat.transports.smallwebrtc.connection import IceServer

from gotiny.agent.persona import Persona
from gotiny.core.logging import configure, get_logger
from gotiny.core.settings import settings
from gotiny.gateway.api import health, offer, playground
from gotiny.gateway.services.lifecycle import Lifecycle
from gotiny.gateway.services.sessions import SessionManager

log = get_logger("gotiny.gateway")


def _ice_servers() -> list[IceServer]:
    """STUN is enough on a LAN. A real caller behind carrier NAT needs TURN,
    which is a Phase 1 concern alongside telephony."""
    urls = os.getenv("GOTINY_STUN_URLS", "stun:stun.l.google.com:19302")
    return [IceServer(urls=u.strip()) for u in urls.split(",") if u.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure(settings.log_level, json_output=settings.env != "local")
    persona = Persona.load()
    sessions = SessionManager(max_concurrent=settings.max_concurrent_calls)
    lifecycle = Lifecycle(sessions)

    app.state.persona = persona
    app.state.sessions = sessions
    app.state.lifecycle = lifecycle
    app.state.ice_servers = _ice_servers()

    log.info(
        "gateway_ready",
        persona=persona.slug,
        language=persona.language,
        voice=persona.voice_id,
        capacity=settings.max_concurrent_calls,
        tts=settings.tts_url,
        stt=settings.stt_url,
        llm=f"{settings.llm_model} @ {settings.llm_base_url}",
    )
    yield

    # Shutdown. uvicorn runs this as part of its own SIGTERM handling, which is
    # why we do NOT install signal handlers of our own -- doing so replaces
    # uvicorn's and the process drains but never exits.
    await lifecycle.drain()
    log.info("gateway_stopped", **sessions.snapshot())


app = FastAPI(title="gotiny-gateway", lifespan=lifespan)

app.include_router(health.router)
app.include_router(offer.router)
app.include_router(playground.router)
