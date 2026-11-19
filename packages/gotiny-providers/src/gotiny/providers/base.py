"""Provider protocols. Structural typing — no inheritance required."""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from gotiny.providers.caps import ProviderCaps, ProviderHealth
from gotiny.providers.wire import STTRequest, STTResponse, TTSEvent, TTSRequest


@runtime_checkable
class TTSBackend(Protocol):
    caps: ProviderCaps

    def stream(self, req: TTSRequest) -> AsyncIterator[TTSEvent]:
        """Yield >=1 AudioChunk then exactly one StreamDone.

        Must raise UnsupportedLanguage if req.language is not in caps.languages.
        """
        ...

    async def cancel(self, request_id: str) -> None: ...

    async def health(self) -> ProviderHealth: ...


@runtime_checkable
class STTBackend(Protocol):
    caps: ProviderCaps

    async def transcribe(self, audio: bytes, req: STTRequest) -> STTResponse: ...

    async def health(self) -> ProviderHealth: ...
