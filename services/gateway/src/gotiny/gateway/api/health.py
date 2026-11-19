"""Liveness plus the live call table.

Deliberately more than "ok": during a drain a load balancer needs to know we are
no longer accepting, and while debugging you want the end-reason tally without a
database. Week 2 moves the tally to SQL; until then this is the only place it
exists.
"""

from fastapi import APIRouter, Request, Response

router = APIRouter()


@router.get("/health")
async def health(request: Request, response: Response) -> dict[str, object]:
    state = request.app.state
    snap = state.sessions.snapshot()
    if not snap["accepting"]:
        response.status_code = 503  # drain: take me out of rotation
    return {
        "status": "ok" if snap["accepting"] else "draining",
        "persona": state.persona.slug,
        "language": state.persona.language,
        **snap,
    }
