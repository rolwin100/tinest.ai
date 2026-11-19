"""Tool registry: name -> (schema, handler).

Personas reference tools by name. Tool *code* lives in the image and is
referenced from config, so adding a tool is a deploy but rewiring which tools an
agent has is not (ADR 0003).
"""

from collections.abc import Callable
from typing import Any

from pipecat.adapters.schemas.function_schema import FunctionSchema

from gotiny.agent.tools.clinic import book_appointment, check_slots

_TOOLS: dict[str, tuple[FunctionSchema, Callable[..., Any]]] = {
    "check_slots": (
        FunctionSchema(
            name="check_slots",
            description="List available appointment slots for a given date.",
            properties={
                "date": {
                    "type": "string",
                    "description": "Date as YYYY-MM-DD. Defaults to tomorrow.",
                }
            },
            required=[],
        ),
        check_slots,
    ),
    "book_appointment": (
        FunctionSchema(
            name="book_appointment",
            description="Book an appointment once you have the caller's name, date and time.",
            properties={
                "name": {"type": "string", "description": "Caller's full name."},
                "phone": {"type": "string", "description": "Callback number."},
                "date": {"type": "string", "description": "Date as YYYY-MM-DD."},
                "time": {"type": "string", "description": "Time as HH:MM, 24-hour."},
            },
            required=["name", "date", "time"],
        ),
        book_appointment,
    ),
}


def resolve(names: list[str]) -> list[tuple[FunctionSchema, Callable[..., Any]]]:
    missing = [n for n in names if n not in _TOOLS]
    if missing:
        raise KeyError(f"unknown tools {missing}; available: {sorted(_TOOLS)}")
    return [_TOOLS[n] for n in names]
