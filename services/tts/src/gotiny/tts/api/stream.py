"""The synthesis endpoint: WS /v1/tts:stream.

Deliberately one line of work. Everything the connection does lives in
``services.stream``, so the route declaration stays a route declaration.
"""

from fastapi import APIRouter, WebSocket

from gotiny.providers.wire import WIRE_VERSION
from gotiny.tts.services.stream import handle_stream

STREAM_PATH = f"/{WIRE_VERSION}/tts:stream"

router = APIRouter()


@router.websocket(STREAM_PATH)
async def stream(ws: WebSocket) -> None:
    await handle_stream(ws, ws.app.state.router)
