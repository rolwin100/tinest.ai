"""One websocket connection, start to finish.

Split from the synthesis pipeline on purpose: this module owns the socket
lifecycle -- accept, parse the header frame, run the cancel watcher alongside
synthesis, and make sure that watcher dies with the connection. ``synthesis``
owns what the audio is.
"""

import asyncio
import contextlib

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from gotiny.providers.wire import TTSRequest
from gotiny.tts.services.routing import VoiceRouter
from gotiny.tts.services.synthesis import synthesise


async def handle_stream(ws: WebSocket, router: VoiceRouter) -> None:
    await ws.accept()
    try:
        req = TTSRequest.model_validate_json(await ws.receive_text())
    except (ValidationError, WebSocketDisconnect):
        await ws.close(code=1003, reason="malformed header")
        return

    cancelled = asyncio.Event()
    watcher = asyncio.create_task(_watch_cancel(ws, req.request_id, cancelled))
    try:
        await synthesise(ws, router, req, cancelled)
    except WebSocketDisconnect:
        pass
    finally:
        watcher.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await watcher


async def _watch_cancel(ws: WebSocket, request_id: str, cancelled: asyncio.Event) -> None:
    """Read the socket while we synthesise. Barge-in cannot wait for a turn."""
    while not cancelled.is_set():
        try:
            msg = await ws.receive_text()
        except (WebSocketDisconnect, RuntimeError):
            cancelled.set()
            return
        if f'"{request_id}"' in msg or '"cancel"' in msg:
            cancelled.set()
            return
