"""Capability discovery. Clients read what this process can do."""

from fastapi import APIRouter, Request

from gotiny.providers.wire import WIRE_VERSION
from gotiny.stt.services.routing import LanguageRouter

router = APIRouter()


@router.get(f"/{WIRE_VERSION}/caps")
async def caps(request: Request) -> dict[str, object]:
    lang_router: LanguageRouter = request.app.state.router
    return {"wire": WIRE_VERSION, "backends": lang_router.backend_caps()}
