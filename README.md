# gotiny.ai

Voice agents for Indian languages and US English. Self-hosted models, own the stack.

Architecture, tech-stack rationale and the full project structure: [`ARCHITECTURE-PLAN.md`](./ARCHITECTURE-PLAN.md).

## Setup (10 minutes)

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-packages     # or: just install
cp .env.example .env
just conformance           # should pass green against the fake providers
```

That last command is the point of step 1: the contract test suite runs and passes
*before any model exists*. Every provider added later — Kokoro, IndicF5, your own
weights — is held to the same tests.

## Layout

| Path | What |
|---|---|
| `packages/gotiny-core` | settings, ids, logging, shared types |
| `packages/gotiny-providers` | **the swap seam** — registry, caps, wire protocol, Pipecat bridges |
| `bench/conformance` | the suite every provider must pass |
| `docs/adr` | why things are the way they are |

Empty directories with a README are deliberate placeholders — see the plan for what lands where and when.
