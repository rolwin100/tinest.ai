"""The TTS contract. If a provider fails here it does not ship."""

import pytest

from gotiny.core.errors import UnsupportedCapability, UnsupportedLanguage
from gotiny.core.ids import new_request_id
from gotiny.core.types import Language
from gotiny.providers.base import TTSBackend
from gotiny.providers.wire import AudioChunk, StreamDone, TTSRequest

HINDI_TEXT = "नमस्ते। क्या मैं आपकी मदद कर सकती हूँ? कृपया अपना नाम बताइए।"


def _req(backend: TTSBackend, **kw: object) -> TTSRequest:
    lang = kw.pop("language", Language.HINDI)
    return TTSRequest(
        request_id=new_request_id(),
        text=kw.pop("text", HINDI_TEXT),  # type: ignore[arg-type]
        voice_id=kw.pop("voice_id", "hi-female-01"),  # type: ignore[arg-type]
        language=lang,  # type: ignore[arg-type]
        sample_rate=min(backend.caps.sample_rates),
        **kw,  # type: ignore[arg-type]
    )


def test_backend_satisfies_protocol(tts: TTSBackend) -> None:
    assert isinstance(tts, TTSBackend)


def test_caps_are_coherent(tts: TTSBackend) -> None:
    assert tts.caps.modality == "tts"
    assert tts.caps.languages, "a provider serving no languages is misconfigured"
    assert tts.caps.sample_rates
    if tts.caps.chunk_granularity == "frame":
        assert tts.caps.streaming, "frame granularity without streaming is incoherent"


async def test_yields_audio_then_exactly_one_done(tts: TTSBackend) -> None:
    events = [e async for e in tts.stream(_req(tts))]

    assert events, "stream produced nothing at all"
    assert isinstance(events[-1], StreamDone), "StreamDone must be last"
    assert sum(isinstance(e, StreamDone) for e in events) == 1, "exactly one StreamDone"

    chunks = [e for e in events if isinstance(e, AudioChunk)]
    assert chunks, "no audio — a 'successful' silent synthesis is the worst failure mode"
    assert all(c.data for c in chunks), "empty audio chunk"
    assert [c.seq for c in chunks] == list(range(len(chunks))), "seq must be 0..n-1 in order"


async def test_trailer_accounting_is_sane(tts: TTSBackend) -> None:
    req = _req(tts)
    events = [e async for e in tts.stream(req)]
    done = events[-1]
    assert isinstance(done, StreamDone)
    t = done.trailer

    # These numbers land on the `turn` row. Wrong here means our latency and
    # cost data is wrong forever, and silently.
    assert t.request_id == req.request_id
    assert t.provider == tts.caps.name
    assert t.chars == len(req.text)
    assert t.ttfb_ms > 0
    assert t.audio_ms > 0


async def test_cancel_mid_stream_stops_promptly(tts: TTSBackend) -> None:
    """Barge-in. Contract: 'drop the remaining sentences', not 'stop mid-sample'."""
    full = len([e async for e in tts.stream(_req(tts)) if isinstance(e, AudioChunk)])
    if full < 2:
        pytest.skip("single-chunk provider: nothing to interrupt")

    req = _req(tts)
    got = 0
    async for event in tts.stream(req):
        if isinstance(event, AudioChunk):
            got += 1
            if got == 1:
                await tts.cancel(req.request_id)

    assert got < full, f"cancel ignored: emitted {got} of {full} chunks anyway"


async def test_unsupported_language_raises(tts: TTSBackend) -> None:
    missing = next((lang for lang in Language if lang not in tts.caps.languages), None)
    if missing is None:
        pytest.skip("provider claims every language")
    with pytest.raises(UnsupportedLanguage):
        async for _ in tts.stream(_req(tts, language=missing)):
            pass


async def test_cloning_claim_is_honest(tts: TTSBackend) -> None:
    """A fixed-voice model must refuse, not quietly substitute a default voice."""
    if tts.caps.supports_cloning:
        pytest.skip("provider supports cloning")
    with pytest.raises(UnsupportedCapability):
        async for _ in tts.stream(_req(tts, voice_id="clone:voice_abc123")):
            pass
