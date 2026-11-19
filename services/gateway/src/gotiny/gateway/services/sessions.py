"""The live call table: who is on the phone right now, and how many more we take.

A hard cap that rejects cleanly beats an open door that degrades every call in
flight. One caller hearing "we're busy" is a far better outcome than forty
callers hearing stuttering audio because the box is oversubscribed.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from gotiny.agent.bot import CallResult
from gotiny.core.errors import GotinyError
from gotiny.core.logging import get_logger

log = get_logger("gotiny.gateway.sessions")


class AtCapacity(GotinyError):
    """Refused because the box is full. Retryable elsewhere, not here."""


@dataclass
class Session:
    call_id: str
    task: asyncio.Task
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SessionManager:
    def __init__(self, max_concurrent: int) -> None:
        self._max = max_concurrent
        self._live: dict[str, Session] = {}
        self._accepting = True
        self._drained = asyncio.Event()
        self._drained.set()
        self.completed: list[CallResult] = []

    @property
    def live(self) -> int:
        return len(self._live)

    @property
    def accepting(self) -> bool:
        return self._accepting

    def check_admission(self) -> None:
        """Raise rather than return a bool: refusing a call is an event, not a flag."""
        if not self._accepting:
            raise AtCapacity("draining; not accepting new calls")
        if self.live >= self._max:
            raise AtCapacity(f"at capacity ({self.live}/{self._max})")

    def add(self, call_id: str, task: asyncio.Task) -> Session:
        session = Session(call_id=call_id, task=task)
        self._live[call_id] = session
        self._drained.clear()
        task.add_done_callback(lambda t, cid=call_id: self._reap(cid, t))
        log.info("call_started", call_id=call_id, live=self.live, cap=self._max)
        return session

    def _reap(self, call_id: str, task: asyncio.Task) -> None:
        self._live.pop(call_id, None)
        if not task.cancelled():
            result = task.exception() or task.result()
            if isinstance(result, CallResult):
                self.completed.append(result)
        if not self._live:
            self._drained.set()
        log.info("call_finished", call_id=call_id, live=self.live)

    def stop_accepting(self) -> None:
        self._accepting = False

    async def wait_drained(self, deadline_secs: float) -> bool:
        """True if everyone hung up in time; False if we had to cut them off."""
        try:
            await asyncio.wait_for(self._drained.wait(), timeout=deadline_secs)
            return True
        except TimeoutError:
            return False

    def cancel_all(self) -> None:
        for session in list(self._live.values()):
            session.task.cancel()

    def snapshot(self) -> dict:
        return {
            "live": self.live,
            "capacity": self._max,
            "accepting": self._accepting,
            "completed": len(self.completed),
            "end_reasons": _tally(self.completed),
        }


def _tally(results: list[CallResult]) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in results:
        out[r.end_reason] = out.get(r.end_reason, 0) + 1
    return out
