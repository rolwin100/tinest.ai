# ADR 0003 — The database is the authority for agent configuration

**Status:** accepted · **Date:** 2026-08-21

## Context
Agent behaviour (prompt, voice, language, tools, model bindings) could live in
repo YAML, in the database, or in a console editor. Having two of the three is
how you get three sources of truth.

## Decision
`agent_version` rows hold the resolved config JSON and are immutable.
`services/agent/pipeline.py` takes an `agent_version_id`, loads it at call start,
and writes that id onto the `call` row. `deploy/seeds/*.yaml` is an **import
fixture only** — never read at runtime.

## Why
- "Changing a prompt does not need a deploy" is only true if the prompt is a row.
- Every call is attributable to the exact config that produced it, which is what
  makes A/B comparison and regression triage possible at all.
- The console config editor and the seed files cannot disagree, because one of
  them is not a source.

## Consequence
Tool *code* stays in the agent image and is referenced by name from config.
Adding a tool is a deploy; rewiring which tools an agent has is not.
