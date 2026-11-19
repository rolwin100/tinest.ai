"""Liveness. Answers ``ok`` only once weights are in memory.

That is the whole point of loading in ``lifespan``: a load balancer that gets a
200 here must be able to assume the next synthesis request will not pay for a
cold model.
"""

from fastapi import APIRouter, Request

from gotiny.providers.wire import WIRE_VERSION
from gotiny.tts.services.routing import VoiceRouter

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict:
    voice_router: VoiceRouter = request.app.state.router
    return {
        "status": "ok",
        "wire": WIRE_VERSION,
        "backends": [c["name"] for c in voice_router.backend_caps()],
    }
