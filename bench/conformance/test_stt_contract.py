"""The STT contract."""

import pytest

from gotiny.core.errors import UnsupportedLanguage
from gotiny.core.ids import new_request_id
from gotiny.core.types import Language
from gotiny.providers.base import STTBackend
from gotiny.providers.wire import STTRequest


def _audio(sample_rate: int, ms: int = 1_500) -> bytes:
    return b"\x00\x01" * int(sample_rate * ms / 1_000)


def test_backend_satisfies_protocol(stt: STTBackend) -> None:
    assert isinstance(stt, STTBackend)
    assert stt.caps.modality == "stt"


async def test_transcribes_and_reports_audio_duration(stt: STTBackend) -> None:
    rate = min(stt.caps.sample_rates)
    req = STTRequest(request_id=new_request_id(), language=Language.HINGLISH, sample_rate=rate)
    res = await stt.transcribe(_audio(rate), req)

    assert res.request_id == req.request_id
    assert res.provider == stt.caps.name
    assert res.text.strip(), "empty transcript on speech-bearing audio"
    # audio_ms feeds per-minute COGS; a wrong value corrupts pricing.
    assert 1_400 < res.audio_ms < 1_600, f"expected ~1500ms, got {res.audio_ms}"


async def test_unsupported_language_raises(stt: STTBackend) -> None:
    missing = next((lang for lang in Language if lang not in stt.caps.languages), None)
    if missing is None:
        pytest.skip("provider claims every language")
    rate = min(stt.caps.sample_rates)
    req = STTRequest(request_id=new_request_id(), language=missing, sample_rate=rate)
    with pytest.raises(UnsupportedLanguage):
        await stt.transcribe(_audio(rate), req)
