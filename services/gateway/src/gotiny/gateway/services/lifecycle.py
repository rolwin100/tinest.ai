"""Draining: stop accepting, let live calls finish, then exit.

The honest version of "deploys do not drop calls": model *servers* deploy
independently because they are separate processes, but a gateway deploy drains.
Hanging up on someone mid-sentence to ship a commit is not acceptable, and a
deploy that waits forever is not either -- hence a deadline.

**Why this is not a signal handler.** The obvious implementation registers a
SIGTERM handler on the event loop. It works, and it is wrong: ``add_signal_handler``
*replaces* uvicorn's handler, so the drain completes and the process then sits
there forever, because nothing is left to shut the server down. Found by killing
a running gateway and watching it refuse to die.

Instead we drain in the shutdown half of the lifespan, which uvicorn runs *as
part of* its own SIGTERM handling. WebRTC media does not flow through uvicorn's
HTTP sockets, so live calls survive its connection teardown while we wait.
"""

import asyncio

from gotiny.core.logging import get_logger
from gotiny.gateway.services.sessions import SessionManager

log = get_logger("gotiny.gateway.lifecycle")

DRAIN_DEADLINE_SECS = 30.0


class Lifecycle:
    def __init__(self, sessions: SessionManager, deadline: float = DRAIN_DEADLINE_SECS) -> None:
        self._sessions = sessions
        self._deadline = deadline
        # Bots watch this so a drain asks them to wrap up rather than severing.
        self.stop = asyncio.Event()

    async def drain(self) -> None:
        """Called from lifespan shutdown. Returns when calls end or time out."""
        live = self._sessions.live
        self._sessions.stop_accepting()
        self.stop.set()
        if not live:
            log.info("drain_nothing_live")
            return

        log.info("drain_started", live=live, deadline_s=self._deadline)
        finished = await self._sessions.wait_drained(self._deadline)
        if finished:
            log.info("drained_cleanly")
        else:
            log.warning("drain_deadline_exceeded", live=self._sessions.live)
            self._sessions.cancel_all()
