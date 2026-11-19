"""In-memory providers so the suite is runnable on day 1, with no models installed.

Two TTS fakes on purpose, because our real fleet has both shapes:

* ``FakeFrameTTS``     - streaming, frame granularity   (Kokoro-like)
* ``FakeUtteranceTTS`` - non-streaming, one chunk/sentence (IndicF5-like)

If the contract only fitted the streaming shape we would not notice until
IndicF5 arrived in week 3.
"""

import asyncio
import re
from collections.abc import AsyncIterator

from gotiny.core.errors import UnsupportedCapability, UnsupportedLanguage
from gotiny.core.types import Language
from gotiny.providers.caps import ProviderCaps, ProviderHealth
from gotiny.providers.wire import (
    AudioChunk,
    StreamDone,
    STTRequest,
    STTResponse,
    TTSEvent,
    TTSRequest,
    TTSTrailer,
)

_INDIC = frozenset({Language.HINDI, Language.HINGLISH, Language.ENGLISH_IN})


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?।])\s+", text.strip()) if s]


class _BaseFakeTTS:
    caps: ProviderCaps

    def __init__(self) -> None:
        self._cancelled: set[str] = set()

    async def cancel(self, request_id: str) -> None:
        self._cancelled.add(request_id)

    async def health(self) -> ProviderHealth:
        return ProviderHealth(name=self.caps.name, healthy=True)

    def _check(self, req: TTSRequest) -> None:
        if not self.caps.supports(req.language):
            raise UnsupportedLanguage(f"{self.caps.name} cannot serve {req.language}")
        if req.voice_id.startswith("clone:") and not self.caps.supports_cloning:
            raise UnsupportedCapability(f"{self.caps.name} is a fixed-voice model")


class FakeFrameTTS(_BaseFakeTTS):
    """Streaming, 20 ms frames. Stands in for Kokoro."""

    caps = ProviderCaps(
        name="fake-frame@1.0",
        modality="tts",
        languages=_INDIC | {Language.ENGLISH_US},
        sample_rates=frozenset({8_000, 24_000}),
        streaming=True,
        supports_cloning=False,
        chunk_granularity="frame",
    )

    async def stream(self, req: TTSRequest) -> AsyncIterator[TTSEvent]:
        self._check(req)
        frame = b"\x00\x01" * int(req.sample_rate * 0.02)  # 20 ms of s16le
        n = max(1, len(req.text) // 4)
        emitted = 0
        for seq in range(n):
            if req.request_id in self._cancelled:
                break
            await asyncio.sleep(0)
            yield AudioChunk(data=frame, seq=seq)
            emitted += 1
        yield StreamDone(
            trailer=TTSTrailer(
                request_id=req.request_id,
                ttfb_ms=12.0,
                audio_ms=emitted * 20.0,
                chars=len(req.text),
                provider=self.caps.name,
            )
        )


class FakeUtteranceTTS(_BaseFakeTTS):
    """Non-streaming, one chunk per sentence, and it CAN clone. Stands in for IndicF5."""

    caps = ProviderCaps(
        name="fake-utterance@1.0",
        modality="tts",
        languages=_INDIC,
        sample_rates=frozenset({8_000, 24_000}),
        streaming=False,
        supports_cloning=True,
        chunk_granularity="sentence",
    )

    async def stream(self, req: TTSRequest) -> AsyncIterator[TTSEvent]:
        self._check(req)
        total = 0
        for seq, sentence in enumerate(_sentences(req.text) or [req.text]):
            if req.request_id in self._cancelled:
                break  # cancel == drop remaining sentences
            await asyncio.sleep(0)
            samples = int(req.sample_rate * 0.05 * max(1, len(sentence) // 10))
            yield AudioChunk(data=b"\x00\x01" * samples, seq=seq)
            total += samples * 2
        yield StreamDone(
            trailer=TTSTrailer(
                request_id=req.request_id,
                ttfb_ms=180.0,
                audio_ms=(total / (req.sample_rate * 2)) * 1000,
                chars=len(req.text),
                provider=self.caps.name,
            )
        )


class FakeSTT:
    caps = ProviderCaps(
        name="fake-stt@1.0",
        modality="stt",
        languages=_INDIC,
        sample_rates=frozenset({8_000, 16_000}),
        streaming=False,
    )

    async def health(self) -> ProviderHealth:
        return ProviderHealth(name=self.caps.name, healthy=True)

    async def transcribe(self, audio: bytes, req: STTRequest) -> STTResponse:
        if not self.caps.supports(req.language):
            raise UnsupportedLanguage(f"{self.caps.name} cannot serve {req.language}")
        return STTResponse(
            request_id=req.request_id,
            text="namaste, appointment book karni hai",
            language=req.language,
            audio_ms=(len(audio) / (req.sample_rate * 2)) * 1000,
            provider=self.caps.name,
        )
