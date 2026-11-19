# Conformance

One suite. Every provider passes it — Kokoro, IndicF5, a Qwen3-TTS baseline, and
in Phase 2 our own weights. A provider that cannot pass does not ship.

It exists before any real model does, which is the point: it imports only
`gotiny-providers`, so it can test backends that did not exist when it was written.

Add a provider by appending a factory to `TTS_BACKENDS` / `STT_BACKENDS` in
`conftest.py`. Factories that need a running server should return `None` when
unreachable — the suite skips rather than fails, so `just conformance` stays
green on a laptop with nothing running.

## What is asserted, and why each one is here

| Test | Why it exists |
|---|---|
| chunk ordering | a stream that yields `StreamDone` before audio, or twice, breaks playback |
| audio is non-empty | a backend that "succeeds" with silence is the worst failure mode: invisible |
| trailer accounting | `ttfb_ms` / `audio_ms` / `chars` land on the `turn` row — wrong here means wrong cost and latency data forever |
| **cancel mid-stream** | barge-in. The single feature that separates a demo from a product |
| language rejection | must raise `UnsupportedLanguage`, never silently synthesise the wrong thing |
| caps honesty | a backend claiming `supports_cloning=False` must refuse to clone, not substitute a default voice |
| duplicate registry keys | two providers sharing an id makes `GROUP BY provider` lie |
