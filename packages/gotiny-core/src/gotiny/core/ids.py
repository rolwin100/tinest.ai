"""Prefixed, sortable ids. Prefixes make log grepping and bug reports survivable."""

import uuid


def _new(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"


def new_call_id() -> str:
    return _new("call")


def new_turn_id() -> str:
    return _new("turn")


def new_request_id() -> str:
    """One per model request. Carried on the wire so a slow hop is traceable."""
    return _new("req")


def new_voice_id() -> str:
    return _new("voice")
