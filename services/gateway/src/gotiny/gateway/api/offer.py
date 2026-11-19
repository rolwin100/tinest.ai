"""POST /offer -- WebRTC signaling, and the only way a call begins.

SmallWebRTCTransport does not bring a server: Pipecat ships a *development*
runner, and this is the production equivalent. Signaling is also the only place
capacity can be enforced, because it is the last moment we can still say no.
"""

import asyncio

from fastapi import APIRouter, HTTPException, Request
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pydantic import BaseModel

from gotiny.agent.bot import run_call
from gotiny.core.ids import new_call_id
from gotiny.core.logging import get_logger
from gotiny.gateway.services.sessions import AtCapacity

log = get_logger("gotiny.gateway.offer")

router = APIRouter()


class Offer(BaseModel):
    sdp: str
    type: str


class Answer(BaseModel):
    call_id: str
    sdp: str
    type: str


@router.post("/offer", response_model=Answer)
async def offer(body: Offer, request: Request) -> Answer:
    state = request.app.state
    try:
        state.sessions.check_admission()
    except AtCapacity as e:
        # 503 with Retry-After, not a silent queue. A caller told "busy" can call
        # back; a caller held in a queue hears dead air.
        raise HTTPException(status_code=503, detail=str(e), headers={"Retry-After": "5"}) from e

    call_id = new_call_id()
    connection = SmallWebRTCConnection(ice_servers=state.ice_servers)
    await connection.initialize(sdp=body.sdp, type=body.type)

    task = asyncio.create_task(
        run_call(call_id, state.persona, connection, stop=state.lifecycle.stop),
        name=f"call:{call_id}",
    )
    state.sessions.add(call_id, task)

    # NB: initialize() is a coroutine, get_answer() is NOT. Awaiting it raises
    # "object dict can't be used in 'await' expression".
    answer = connection.get_answer()
    log.info("offer_answered", call_id=call_id, live=state.sessions.live)
    return Answer(call_id=call_id, sdp=answer["sdp"], type=answer["type"])
