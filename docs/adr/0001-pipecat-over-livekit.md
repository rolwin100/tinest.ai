# ADR 0001 — Pipecat for orchestration, not LiveKit Agents (yet)

**Status:** accepted · **Date:** 2026-08-21

## Context
Both are open-source, self-hostable, and reach sub-500 ms. We develop on a
MacBook with no telephony accounts for the first four weeks.

## Decision
Pipecat 1.7 with `SmallWebRTCTransport`.

## Why
- Local-first: browser mic to Python process with zero accounts.
- Ships the extras we need now (`whisper`, `kokoro`, `silero`, `local-smart-turn`,
  `tracing`, `sentry`, `pgmq`), so week 1 is configuration, not implementation.
- Built-in TTFB/usage metrics and interruption handling — the exact spans our
  latency budget is measured against. Subclassing beats rebuilding.
- Native sentence-level LLM-to-TTS streaming.

## What we give up
LiveKit's native SIP and phone-numbers product. That is the strongest argument
for switching, and it only pays off at Phase 1 when a customer needs a number.

## How we keep the option open
All transport code is confined to `services/agent/transports/`. Switching is
days, not weeks. Revisit at first telephony customer.
