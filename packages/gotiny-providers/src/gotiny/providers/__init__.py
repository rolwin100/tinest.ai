"""The swap seam.

Nothing outside this package imports a model library. ``services/agent`` imports
only from here, which is what makes replacing IndicF5 with our own weights a
registry entry plus a config value.
"""

from gotiny.providers.base import STTBackend, TTSBackend
from gotiny.providers.caps import ProviderCaps, ProviderHealth
from gotiny.providers.registry import available, get, register
from gotiny.providers.wire import (
    WIRE_VERSION,
    AudioChunk,
    StreamDone,
    STTRequest,
    STTResponse,
    TTSCancel,
    TTSError,
    TTSRequest,
    TTSTrailer,
)

__all__ = [
    "WIRE_VERSION",
    "AudioChunk",
    "ProviderCaps",
    "ProviderHealth",
    "STTBackend",
    "STTRequest",
    "STTResponse",
    "StreamDone",
    "TTSBackend",
    "TTSCancel",
    "TTSError",
    "TTSRequest",
    "TTSTrailer",
    "available",
    "get",
    "register",
]
