"""Liveness. Answers ``ok`` only once weights are in memory."""

from fastapi import APIRouter, Request

from gotiny.providers.wire import WIRE_VERSION
from gotiny.stt.services.routing import LanguageRouter

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    lang_router: LanguageRouter = request.app.state.router
    return {"status": "ok", "wire": WIRE_VERSION, "backends": lang_router.names}
