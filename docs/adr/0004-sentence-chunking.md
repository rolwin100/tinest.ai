# ADR 0004 — Sentence-level chunking, and cancel means "drop the rest"

**Status:** accepted · **Date:** 2026-08-21

## Context
Our primary Indic voice is IndicF5 — an F5-family flow-matching model. It is
non-autoregressive: it synthesises a whole utterance at once, conditioned on
`(ref_audio, ref_text)`. It cannot emit sub-sentence audio. Kokoro, by contrast,
streams frames.

## Decision
1. The wire contract's chunk granularity is **sentence-level**. Providers may be
   finer (`chunk_granularity="frame"`) but nothing may *require* finer.
2. Cancellation semantics are **"stop after the current sentence, drop the
   remainder"** — not "stop mid-sample".
3. Reference audio and reference text are resolved **server-side** from a stable
   logical `voice_id`. Reference material never travels in a request.
4. TTS TTFB targets stay **unset** until `bench/tts_eval` measures IndicF5. For a
   full-utterance model, TTFB is first-sentence synthesis time.

## Why
A contract that assumes frame streaming would exclude our most important model.
A cancel contract that assumes mid-sample interruption would be unimplementable
by half the fleet — and untestable, which is worse.

## Consequence
Barge-in is a *contract* requirement, asserted in `bench/conformance`, not a
feature bolted on later. Two fakes exist (`FakeFrameTTS`, `FakeUtteranceTTS`)
precisely so both shapes are exercised before either real model arrives.
