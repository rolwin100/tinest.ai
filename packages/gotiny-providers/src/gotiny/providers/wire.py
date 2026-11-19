"""The HTTP/WS contract our own model servers speak.

This is the durable seam: in Phase 2 our own weights must satisfy exactly this,
which is what makes swapping them in a config change rather than a refactor.

Design note — Pydantic guards the *header* and the *trailer* only. Audio travels
as raw binary WS frames. Validating and base64-ing a model per 20-50 ms of audio
would burn both latency and CPU on the hottest path we have.
"""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from gotiny.core.types import Language

WIRE_VERSION = "v1"


class TTSRequest(BaseModel):
    """Sent as one JSON frame to open a synthesis stream."""

    request_id: str
    text: str
    voice_id: str = Field(
        description="Logical, stable name (e.g. 'hi-female-01'). Resolution to "
        "reference audio / speaker embedding is the TTS server's job — reference "
        "material never travels in a request."
    )
    language: Language
    sample_rate: int = 24_000
    speed: float = 1.0


class TTSTrailer(BaseModel):
    """Final JSON frame. Carries the numbers that end up on the ``turn`` row."""

    request_id: str
    done: bool = True
    ttfb_ms: float
    audio_ms: float
    chars: int
    provider: str


class TTSCancel(BaseModel):
    """Barge-in.

    Semantics are 'stop after the current sentence and drop the rest' — not
    'stop mid-sample'. That is what interruption actually needs, and it is
    honourable by non-streaming backends too (IndicF5 synthesises whole
    utterances), so the contract holds across the whole fleet.
    """

    cancel: str


class TTSError(BaseModel):
    """Sent instead of a trailer when synthesis cannot proceed.

    ``kind`` mirrors the names in ``gotiny.core.errors`` on purpose. The error
    taxonomy is organised by how the caller should *respond* -- retry, fail over,
    or never retry -- and that distinction has to survive the process boundary or
    the client is reduced to guessing from a string.
    """

    request_id: str
    error: str
    kind: Literal["unsupported_language", "unsupported_capability", "unknown_voice", "internal"]


class STTRequest(BaseModel):
    request_id: str
    language: Language
    sample_rate: int = 16_000


class STTResponse(BaseModel):
    request_id: str
    text: str
    language: Language
    is_final: bool = True
    audio_ms: float
    provider: str
    confidence: float | None = None


# ── stream events (hot path: dataclasses, not models) ──


@dataclass(slots=True)
class AudioChunk:
    data: bytes
    seq: int


@dataclass(slots=True)
class StreamDone:
    trailer: TTSTrailer


TTSEvent = AudioChunk | StreamDone
