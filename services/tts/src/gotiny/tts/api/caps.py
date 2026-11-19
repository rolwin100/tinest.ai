"""Capability discovery.

Clients read what this process can do rather than hardcoding it. A client that
hardcodes caps will eventually disagree with the server, and the disagreement
surfaces as mysterious synthesis failures.
"""

from fastapi import APIRouter, Request

from gotiny.providers.wire import WIRE_VERSION
from gotiny.tts.services.routing import VoiceRouter

router = APIRouter()


@router.get(f"/{WIRE_VERSION}/caps")
async def caps(request: Request) -> dict:
    voice_router: VoiceRouter = request.app.state.router
    return {
        "wire": WIRE_VERSION,
        "backends": voice_router.backend_caps(),
        "voices": [v.model_dump(mode="json") for v in voice_router.voices.all()],
    }
