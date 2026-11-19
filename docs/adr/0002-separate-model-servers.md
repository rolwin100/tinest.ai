# ADR 0002 — Model servers are separate processes, from day one

**Status:** accepted · **Date:** 2026-08-21

## Context
The tempting shortcut is loading Whisper and Kokoro in-process inside the
Pipecat pipeline. It works on a Mac and costs weeks later.

## Decision
`services/tts` and `services/stt` are separate processes behind a versioned
WS/HTTP contract. **Locally they run as host uvicorn processes, not containers**
— macOS Docker has no Metal/MPS access. Same FastAPI app, same route; the
container appears only for the Linux/CUDA box.

## Why
- Independent GPU scaling: TTS and STT have different utilisation curves.
- Independent deploy: a new TTS checkpoint must not restart in-flight calls.
- No event-loop blocking: a synchronous forward pass inside the agent's asyncio
  loop destroys the latency budget under concurrency.
- A real seam to measure: first-byte latency per model is observable at the
  boundary, which is the number Phase 2 optimises.

## Consequence
The HTTP path is the default from week 1, on the laptop too. In-process adapters
exist only as an opt-in `just dev-fast` escape hatch. Deferring the HTTP path to
week 4 would make "swap the adapter name" a rewrite instead of a config change.
