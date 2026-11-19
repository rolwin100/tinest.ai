"""Shared primitives for gotiny.ai. Imported by every other package.

The .env load happens here, before anything else, because module-level
``os.getenv`` calls elsewhere run at *their* import time -- and by then it is
too late to fill the environment in.
"""

# ruff: noqa: E402 - the .env load must precede every other import.
from gotiny.core.paths import load_env as _load_env

_load_env()

from gotiny.core.ids import new_call_id, new_request_id, new_turn_id
from gotiny.core.settings import Settings, settings
from gotiny.core.types import AudioFormat, Language

__all__ = [
    "AudioFormat",
    "Language",
    "Settings",
    "new_call_id",
    "new_request_id",
    "new_turn_id",
    "settings",
]
