"""Mock clinic tools.

Fake data on purpose. The *structure* is what matters now -- that the LLM can
call a function, that the result comes back into the context, and that the call
is timed. Real calendar and CRM integration arrives in Phase 1, and when it does
these keep their signatures and change only their bodies.

Note what these do NOT do: hold customer credentials. In Phase 1 they call
``services/api``, which owns the CRM token, the retry and the idempotency key.
A per-call bot is not a place a customer's credentials should live.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from gotiny.core.logging import get_logger

log = get_logger("gotiny.agent.tools")

_SLOTS = ["10:00", "10:30", "11:00", "15:30", "16:00", "17:15"]


async def check_slots(params: Any) -> None:
    """Return appointment slots for a date. Registered as an LLM function."""
    args = getattr(params, "arguments", {}) or {}
    day = args.get("date") or (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")
    log.info("tool_check_slots", date=day)
    await params.result_callback({"date": day, "available": _SLOTS})


async def book_appointment(params: Any) -> None:
    """Book a slot. Fake, but shaped like the real thing."""
    args = getattr(params, "arguments", {}) or {}
    name = args.get("name", "")
    phone = args.get("phone", "")
    day = args.get("date", "")
    time = args.get("time", "")
    log.info("tool_book_appointment", name=name, date=day, time=time)
    if not (name and day and time):
        await params.result_callback(
            {"ok": False, "reason": "need a name, a date and a time before booking"}
        )
        return
    await params.result_callback(
        {
            "ok": True,
            "confirmation": f"BK-{abs(hash((name, day, time))) % 100000:05d}",
            "name": name,
            "phone": phone,
            "date": day,
            "time": time,
        }
    )
