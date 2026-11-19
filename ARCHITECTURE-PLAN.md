# gotiny.ai — Application Architecture, Tech Stack & Project Structure

**Prepared for:** Rolwin · **Date:** 20 August 2026 · **Rev 3** (adversarial review + TTS/voice-cloning decisions)
**Scope decisions taken:** single monorepo · Phase-0-shaped with Phase-1/2 seams already cut · Next.js console from the start · plan only, no scaffolding yet

Structural companion to `voice-ai-startup-plan.md` (strategy) and `phase-0-build-guide.md` (week-by-week). It answers one question: **what do I create, where does it live, and why won't it need rewriting when my own models arrive?**

---

## 1. Six principles that drive every decision below

1. **The models are replaceable; the seam is not.** Every model sits behind one seam — an HTTP/WS wire contract for the model servers, and a Pipecat service subclass on the pipeline side. Swapping IndicF5 for `gotiny-tts@0.1` in Phase 2 is a registry entry plus a config change.
2. **Three planes, hard-separated.** Media plane (per-call, latency-critical, GPU), control plane (CRUD, boring, cheap), research plane (offline, batch, GPU bursts). Different scaling curves, different failure modes, different deploy cadences. Mixing them is the mistake that forces a rewrite at Phase 2.
3. **Latency and cost are columns, not log lines.** Per-hop timings *and* per-hop consumption (tokens, chars, audio-ms) are written to a `turn` row on every turn. "Did the new TTS regress?" and "what does a call cost?" become `GROUP BY` queries. A self-hosting thesis you can't cost is a guess.
4. **Local and cloud run the same code path.** No "we'll wire up the real path in week 4." The HTTP adapter is the default from week 1, even on the Mac.
5. **The eval harness is repo furniture.** `bench/` exists in week 1. No model swap ships without conformance + benchmark, with confidence intervals.
6. **Defer distributed systems ruthlessly.** One GPU box, docker compose, Postgres. No Kubernetes, no broker, no service mesh until utilisation forces it. Structure is k8s-*ready* without being k8s-*dependent*.

---

## 2. Application architecture

### 2.1 The three planes

```
┌─ MEDIA PLANE ──────────────────────────────── per-call · <800ms budget · GPU ─┐
│  Caller  (browser mic → Phase 1: PSTN/SIP)                                    │
│      │                                                                        │
│      ▼                                                                        │
│  GATEWAY   signaling (SDP offer/answer) · concurrency cap · warm bot pool ·    │
│            supervise + drain                                                  │
│      │ hands off a pre-warmed process                                         │
│      ▼                                                                        │
│  BOT WORKER  (Pipecat pipeline, one process per call)                         │
│      ├─ VAD + turn policy      Silero + local smart-turn                      │
│      ├─ STT service ──────────► stt server    (faster-whisper / IndicConformer)│
│      ├─ LLM service ──────────► llm server    (Ollama → vLLM)                 │
│      ├─ tools ────────────────► api           (check_slots, book_appointment)  │
│      └─ TTS service ──────────► tts server    (Kokoro / IndicF5 → yours)       │
│      │                                                                        │
│      ├──► turn rows, batched off the critical path ──► api ──► Postgres        │
│      └──► dual-channel recording ────────────────────► object storage          │
└───────────────────────────────────────────────────────────────────────────────┘
           │                                              │
┌─ CONTROL PLANE ─── CRUD · seconds are fine ─┐  ┌─ RESEARCH PLANE ─ offline ──┐
│  api (FastAPI): agents · agent_versions ·   │  │  data ingest & cleaning     │
│  calls · turns · transcripts · webhooks ·   │  │  (AI4Bharat, Emilia, ours)  │
│  internal (turn ingest, tool callbacks)     │  │  training runs (P2+)        │
│  console (Next.js): playground, call log,   │  │  eval reports               │
│  agent config · Postgres · object storage   │  │  ⚠ never imported by media  │
└─────────────────────────────────────────────┘  └─────────────────────────────┘
```

### 2.2 The gateway — the piece that's easy to forget

"One process per call" needs an owner. `SmallWebRTCTransport` requires *you* to implement signaling (Pipecat's dev runner is a development runner, not a server), and a cold Python process importing torch/onnxruntime and warming a model eats the entire latency budget on its first call. So `services/gateway` exists in week 1 and owns:

- **Signaling:** the `POST /offer` → SDP answer route; TURN/STUN config (needed the moment a caller isn't on your LAN).
- **Warm pool:** N idle bot processes, models loaded, waiting. A call is *handed to* a warm process, never starting one.
- **Concurrency cap + backpressure:** a hard `MAX_CONCURRENT_CALLS`; over it, reject cleanly (503 / busy tone) rather than degrading every live call.
- **Supervision + drain:** SIGTERM means stop accepting new calls, let live ones finish to a deadline, then exit. This is the mechanism behind "a new TTS checkpoint must not drop in-flight calls" — and note the honest version: model *servers* deploy independently, but a *bot* deploy drains.
- **`call.end_reason`:** `completed | caller_hangup | agent_error | drained | rejected_capacity`. Without it you cannot tell a bug from a hangup.

### 2.3 Where the model seam actually is

Two layers, and conflating them was the first draft's mistake:

**Pipeline side.** A Pipecat pipeline consumes `TTSService` / `STTService` / `LLMService` frame processors — with frame semantics (`TTSStartedFrame`, `TTSAudioRawFrame`), interruption handling, and *built-in TTFB metrics*. Do not re-invent this: subclass Pipecat's base services and inherit the instrumentation you're trying to build. Pipecat 1.7 already ships `kokoro`, `whisper`, `mlx-whisper`, `silero` and `local-smart-turn` extras — week 1 is configuration, not implementation.

**Wire side.** The real, durable seam is the HTTP/WS contract your own model servers speak. That is what a custom model must satisfy in Phase 2.

```
TTS wire protocol  —  WS /v1/tts:stream
  client → one JSON header frame:
    { request_id, text, voice_id, language, sample_rate, speed }
  server → raw binary frames: PCM s16le mono, sentence-chunked
  server → final JSON frame: { request_id, done: true, ttfb_ms, audio_ms, chars }
  client → { cancel: request_id }   # barge-in: drop remaining sentences
```

Raw binary frames, not a Pydantic model per chunk — validating and base64-ing JSON every 20–50 ms of audio is pure latency and CPU. Pydantic guards the header and the trailer, where it's cheap.

**Chunking is defined as sentence-level, deliberately.** Your primary Indic voice (IndicF5) is a flow-matching, non-autoregressive model: it synthesises a whole utterance at once. It cannot emit sub-sentence audio, and its reference-audio conditioning is a *server-side* concern. So:

- `voice_id` stays a stable logical name (`hi-female-01`). The TTS server's own voice registry resolves it to `(ref_audio, ref_text)` for F5-family backends, or to a speaker embedding for others. Reference material never appears in the request.
- Cancellation semantics are "stop after the current sentence and drop the rest" — which is what barge-in actually needs, and is testable against every backend including non-streaming ones.
- **TTS TTFB targets stay unset until `bench/tts_eval` measures IndicF5.** For a full-utterance model, TTFB ≈ synthesis time for the first sentence. Publishing 200 ms before measuring is how you end up with a sales number you can't hit.

**Provider registry.** All contract implementations live in `packages/gotiny-providers`, keyed `name@semver` (`indicf5@0.3`, `kokoro-onnx@1.0`, `gotiny-tts@0.1`). Both `services/agent` and `bench/conformance` import the registry, so the conformance suite can parametrise over every provider — including ones that don't exist yet. The provider id is written to every `turn` row.

### 2.4 Latency budget

Sequential hops for the first sentence of a response, so they add. Numbers chosen to sum to the target.

| Hop | P0 local (Mac) | P0 cloud target | P3 target |
|---|---|---|---|
| end-of-turn detected | 600 | 300 | 200 (semantic) |
| STT final transcript | 350 | 120 | 80 |
| LLM first token | 450 | 150 | 120 |
| TTS first audio byte | 350 | *TBD — measure first* | 100 |
| network + jitter buffer | 50 | 80 | 60 |
| **voice-to-voice** | **~1.8 s** | **≤800 ms** | **≤500 ms** |

Two notes. End-of-turn detection is the largest line item and the one people forget — it's a tuning problem, not a model problem, which is why it gets its own module. And voice-to-voice is **measured as one span end-to-end**, not summed from the others; the rows are a diagnostic breakdown for when the measured span misses.

### 2.5 Data model

Postgres from week 2. Schema and migrations live in `packages/gotiny-db`, owned by neither service and depended on by both — the gateway/bot writes turns via the API's internal route, so only `api` holds a DB connection in the media path.

| Table | Notes |
|---|---|
| `agent` | logical agent; `agent_version` holds the **resolved config JSON** (prompt, voice map, language set, tool names, model bindings) |
| `agent_version` | immutable. **DB is authoritative for config**; repo YAML is a seed fixture only. `pipeline.py` takes an `agent_version_id`, loads it at call start, writes it onto `call` |
| `call` | direction, from/to, status, duration, `end_reason`, `agent_version_id`, **`consent_to_train`** |
| `turn` | per-hop timings · provider ids · barge-in flag · **consumption:** `llm_input_tokens`, `llm_output_tokens`, `tts_chars`, `tts_audio_ms`, `stt_audio_ms`, `gpu_ms` |
| `price_book` | versioned unit prices. **Cost is derived by query, never written from the media plane** |
| `tool_call` | name, args, result, latency — debugging agents means debugging tools |
| `recording` | storage key, format, sample rate, **separate channels for caller and agent** (mixed audio is near-useless for training) |
| `voice` | owner org · language · tier (`library`/`customer`) · status · storage keys for `ref_audio` + verified `ref_text` |
| `voice_consent` | signed consent artifact per customer-supplied voice: who consented, when, scope, revocation |
| `org`, `user`, `api_key` | Phase 1, not week 2. `api_key` stores a hash, never the key |
| `eval_run`, `eval_result` | mirrors `bench/reports/` |

Turn writes are **batched and flushed off the critical path** — a per-turn awaited INSERT sits inside the 800 ms budget. Fire-and-forget task, flushed at turn end and at call end.

### 2.6 Voice cloning is a capability you already have, not a feature to add

IndicF5 is reference-conditioned: it synthesises *only* from `(ref_audio, ref_text)`. There is no default-voice mode. So your preset Hindi voices are already clones of your commissioned artists' samples, while Kokoro (baked style vectors) cannot clone at any price. Two backends, two capability surfaces — which is what `ProviderCaps.supports_cloning` exists to express and what gates the console UI.

What that costs structurally: **an enrollment pipeline in the control plane.** Uploading a wav is not enough — F5-family models need the reference *transcript*, and a wrong `ref_text` degrades output badly. So enrollment is: upload → ASR to derive `ref_text` → human-verify → quality gate (`gotiny-audio`) → register. That is a `services/worker` job, never a media-plane concern.

**Three tiers, deliberately different risk:**

| Tier | What | Posture |
|---|---|---|
| A — library | commissioned artists, rights owned outright | ship first; this is a licensing asset |
| B — customer's own voice | consented staff/brand voice | ship at Phase 1 with a stored consent artifact + identity check |
| C — self-serve upload-anything | anyone clones any voice | **don't.** On an outbound telephony product this is a fraud surface, and it likely puts you inside the IT Rules 2026 bucket for intermediaries that "enable the creation of synthetically generated information" — labelling, provenance and 3-hour takedown duties. Legal review before it is ever built |

Cheap now, expensive later: `agent_version.ai_disclosure` — a spoken "this is an AI assistant" at call start. A config field in week 1; a retrofit across every persona and contract in month 9.

**And the roadmap consequence.** Lane A (small non-AR, fixed speaker embeddings) **cannot do zero-shot cloning**; Lane B (reference-conditioned) is native. If Tier B is a product commitment, Lane A cannot be your only model. The likely end state is a **two-model fleet** — Lane A for high-volume preset voices (cheap, deterministic, fast) and Lane B for cloned voices (pricier, premium tier) — which is why `gotiny.tts.services.routing` exists and why this gets ADR 0005.

---

## 3. Tech stack, layer by layer

| Layer | Choice | Why | Considered and rejected |
|---|---|---|---|
| Agent language | **Python 3.12** | Pipecat needs ≥3.11; the entire ML ecosystem | Node (no ML story), Go (splits the codebase) |
| Python tooling | **uv** workspaces · `ruff` · `mypy` · `pytest` | one lockfile across *all* members incl. `bench` and `research`; ML-heavy deps isolated in dependency groups so the agent image doesn't inherit torch | Poetry (weaker workspaces), pip-tools |
| Orchestration | **Pipecat 1.7** (`pipecat-ai`, 1 Aug 2026) + `SmallWebRTCTransport` | local-first, zero accounts, native LLM→TTS sentence streaming, built-in TTFB metrics + interruption handling, ships `whisper`/`kokoro`/`silero`/`local-smart-turn`/`tracing`/`sentry`/`pgmq` extras | LiveKit Agents *now* (its native SIP only pays off at Phase 1); Vapi/Retell (resellers — no self-host, no COGS control) |
| Signaling / session | **own `services/gateway`** (FastAPI) | SmallWebRTC needs it; Pipecat's dev runner is not a server | relying on the dev runner in production |
| Telephony (P1) | **LiveKit SIP** or Pipecat + Twilio/Exotel/Plivo | behind `agent/transports/`, so a swap not a migration | deciding before a customer needs a number |
| VAD / turn-taking | **Silero VAD** + Pipecat local smart-turn | biggest latency lever; own module for tuning | raw silence thresholds (robotic) |
| STT (local) | `faster-whisper` (CTranslate2) · `mlx-whisper` on Metal | fast, decent Hinglish out of the box | Whisper via transformers (too slow) |
| STT (cloud) | **IndicConformer** (hybrid CTC-RNNT) vs `whisper-large-v3` — bench decides | per-language Indic checkpoints. ⚠ **offline-only**: needs AI4Bharat's NeMo fork (`nemo-v2` branch, pin the commit), no cache-aware streaming decoder. Design is **VAD-segmented pseudo-streaming**: final-transcript latency ≈ endpoint delay + segment inference | assuming upstream `nemo_toolkit` works; claiming true streaming |
| LLM | **Ollama** locally → **vLLM** (AWQ/FP8) on GPU; current-best ~7B open model, **re-picked at bench time** | OpenAI-compatible both sides, so one adapter | pinning a model name in a doc that outlives it; llama.cpp in prod (throughput); OpenAI API in prod (COGS + data rights) — baseline only |
| TTS (preset voices) | **Kokoro-82M ONNX** (English, Apache-2.0) + **IndicF5** (11 Indic langs, 1,417 hrs) | Kokoro: 82M, real-time on Mac CPU, zero GPU, deterministic non-AR latency, and Pipecat ships a `kokoro` extra. Trained for ~$1k / 500 A100-hrs — i.e. your Phase 2 budget, so living in its constraints *is* research. `indic-parler-tts` (21 langs) and Piper as fallbacks | ElevenLabs/Cartesia in prod (the thing you're replacing) |
| TTS (cloning / Lane B) | **Qwen3-TTS-0.6B-Base** as a `bench` baseline and the Phase 2 fine-tune candidate | Apache-2.0, streaming, 3-second cloning. Best Lane B starting point that exists | Qwen3-TTS as the *week-1* TTS: **no Indic languages** (zh/en/ja/ko/de/fr/ru/pt/es/it), and fine-tuning into Indic is [documented as hard](https://github.com/QwenLM/Qwen3-TTS/issues/323) (Hindi-accented prosody bleed). Also 0.6–1.7B competing for VRAM with a 7B LLM on one L4, and vLLM-Omni measures **P99 TTFA 5.56 s at concurrency 64 on 2×H20** — an AR codec model degrades under batching where an 82M non-AR one doesn't |
| Speech-to-speech | not now | Qwen3-Omni-30B-A3B can speak directly, but a 30B MoE is not your unit economics and collapsing STT+LLM+TTS destroys the seam, per-hop latency attribution and per-hop costing | adopting an omni model before Phase 5 |
| Model serving | one process per model: **FastAPI + WS**, `/v1/tts:stream` | independent GPU scaling & deploys; a real seam to measure. **Runs as a host uvicorn process locally** (macOS Docker has no Metal/MPS) and as a Linux/CUDA container in cloud — same app, same route | in-process models as the default; gRPC (revisit if WS framing shows in traces) |
| Control API | **FastAPI + Pydantic v2 + SQLAlchemy 2 + Alembic** (schema in `packages/gotiny-db`) | same language as the agent; only service holding a DB connection | agent writing to Postgres directly (violates the plane boundary, adds latency) |
| Database | **Postgres 17** (pgvector later) | relational call/turn data | Mongo; SQLite in prod |
| Jobs / queue | **pgmq** on the same Postgres | recording post-processing, corpus export, eval runs. ⚠ compiled extension → custom Postgres image, not bare `postgres:17` | Redis/Celery/NATS on day one |
| Object storage | **Cloudflare R2** (zero egress) · **MinIO** locally | recordings are the asset; egress on a growing audio corpus bites | AWS S3 (egress); local disk (corpus outlives the box) |
| Frontend | **Next.js 16.3** App Router · TypeScript · Tailwind · shadcn/ui · `@pipecat-ai/client-js` + `@pipecat-ai/client-react` + `@pipecat-ai/small-webrtc-transport` (three packages, not one) | playground and console in one app; official SDK handles mic/WebRTC plumbing | Vite SPA (want SSR + auth); hand-rolled WebRTC client |
| Auth | P0: one shared password on the playground. P1: **Clerk** or **Better Auth** with orgs | orgs/roles is where DIY auth costs a month | rolling your own, ever |
| Secrets | **sops + age**, encrypted files in `deploy/secrets/`, decrypted to host env at deploy | one box will hold Postgres creds, R2 keys, an HF token and baseline API keys. `.env.example` is not a mechanism | plaintext `.env` on the box; a secrets manager for one box |
| Observability | **Pipecat's OTel tracing** → one collector. `structlog` JSON logs. **Sentry** | pick *one* trace sink | OTel + Tempo + Langfuse + Sentry all at once in month 1 |
| Config | `pydantic-settings` for infra · **DB `agent_version` for agent behaviour** | prompt/voice changes genuinely need no deploy — because they're rows, not files in an image | YAML-in-image while also having an `agent_version` table and a config UI (three sources of truth) |
| CI | **GitHub Actions**: lint, types, tests, conformance on PR · **nightly bench** posting latency + WER **with bootstrap CIs** to `bench/reports/` | the nightly bench is what keeps quality honest solo | import-linter as CI machinery (a pre-commit grep covers the boundary rules) |
| Deploy | docker compose on one rented GPU box (RunPod/Lambda, Mumbai) | Phase 0/1 reality | Kubernetes now |
| IaC | shell + compose now; **Terraform** at Phase 1 | don't automate infra you change weekly | Terraform for one box |

---

## 4. Project structure

Single monorepo. `uv` workspace for Python (members: `packages/*`, `services/*`, `bench`, `research`), `pnpm` workspace for TypeScript. Python packages share the `gotiny.` namespace, so imports read `from gotiny.providers import get_tts`.

```
gotiny/
├── README.md                    # 10-minute local setup, nothing else
├── pyproject.toml               # uv workspace root
├── uv.lock                      # ONE lockfile — incl. bench + research
├── package.json  pnpm-workspace.yaml
├── justfile                     # just dev · just dev-fast · just bench · just cost
├── docker-compose.yml           # postgres(+pgmq) + minio — models run on the host locally
├── .env.example  .python-version
│
├── packages/                    # ── libraries: importable, no entrypoints ──
│   ├── gotiny-core/             #    settings · telemetry/OTel · ids · logging · errors
│   ├── gotiny-db/               # ★  SQLAlchemy models + alembic/ — single schema owner
│   │   └── src/gotiny/db/
│   │       ├── models/          #    agent · agent_version · call · turn · tool_call ·
│   │       │                    #    recording · voice · voice_consent · price_book ·
│   │       │                    #    eval_run · org · user · api_key
│   │       └── alembic/
│   ├── gotiny-providers/        # ★  THE SWAP SEAM
│   │   └── src/gotiny/providers/
│   │       ├── registry.py      #    name@semver → provider class
│   │       ├── caps.py          #    ProviderCaps: languages · streaming · supports_cloning
│   │       ├── wire.py          #    HTTP/WS header + trailer schemas
│   │       ├── tts/             #    kokoro_local · indicf5_http · qwen3_tts_http (baseline)
│   │       │                    #    · gotiny_tts_http (P2) — all Pipecat TTSService subclasses
│   │       ├── stt/             #    whisper_local · indicconformer_http
│   │       └── llm/             #    openai_compat (covers Ollama + vLLM)
│   └── gotiny-audio/            #    resample · loudness norm · 8k µ-law telephony sim ·
│                                #    channel split · ref-audio quality gate
│                                #    — shared by agent, worker, bench AND research
│
├── services/                    # ── deployable processes, one Dockerfile each ──
│   ├── gateway/                 # ★  signaling · warm bot pool · concurrency cap · drain
│   ├── agent/                   #    MEDIA PLANE — the Pipecat pipeline
│   │   └── src/gotiny/agent/
│   │       ├── bot.py           #    one call, start to finish
│   │       ├── pipeline.py      #    assembles from an agent_version_id
│   │       ├── transports/      #    smallwebrtc → livekit, twilio (P1)
│   │       ├── tools/           #    check_slots · book_appointment · transfer_call
│   │       ├── turn/            #    VAD wiring + end-of-turn policy (tune here)
│   │       ├── disclosure.py    #    "this is an AI assistant" — per agent_version
│   │       ├── recording.py     #    dual-channel capture → object storage
│   │       └── telemetry.py     #    spans + consumption → batched turn ingest
│   ├── api/                     #    CONTROL PLANE — FastAPI
│   │   └── src/gotiny/api/
│   │       ├── routers/         #    agents · agent_versions · calls · transcripts ·
│   │       │                    #    recordings · voices · webhooks · health ·
│   │       │                    #    internal/ (turn ingest, tool callbacks)
│   │       └── schemas/
│   ├── worker/                  # ★  pgmq consumer — the only async-job home
│   │   └── jobs/                #    voice_enrollment · recording_postprocess ·
│   │                            #    corpus_export · eval_run
│   ├── tts/                     #    model server: WS /v1/tts:stream
│   │   └── src/gotiny/tts/
│   │       ├── app.py           #    composition root: lifespan + include_router
│   │       ├── api/             #    health · caps · stream — one APIRouter each
│   │       ├── services/        #    synthesis.py (segment → synth → resample →
│   │       │                    #    trailer) · stream.py (one WS connection +
│   │       │                    #    barge-in watcher) · routing.py (preset voice
│   │       │                    #    → Lane A · cloned voice → Lane B)
│   │       ├── repositories/    #    voices.py — voice_id → ref_audio + ref_text,
│   │       │                    #    from DB + storage (YAML seed until then)
│   │       ├── backends/        #    kokoro · indicf5 · qwen3_tts · gotiny_v0 (P2)
│   │       │                    #    · loader.py — construct + load what's installed
│   │       ├── config/          #    voices.yaml — the seed catalogue
│   │       └── util/            #    segmentation · resample (→ gotiny-audio once
│   │                            #    a second service needs them)
│   ├── stt/                     #    model server: /v1/stt (VAD-segmented)
│   └── llm/                     #    vLLM launch config + thin shim (little own code)
│
├── apps/console/                #    Next.js 16 — playground first, console second
│   ├── app/(playground)/        #    mic UI — the thing you demo to clinics
│   ├── app/(console)/
│   │   ├── calls/               #    list · transcript + audio player · latency & cost
│   │   ├── agents/              #    config editor → writes a new agent_version
│   │   └── voices/              #    enroll · consent capture · quality report · revoke
│   └── lib/api.ts
│
├── research/                    # ── RESEARCH PLANE — never imported by services/ ──
│   ├── data/
│   │   ├── sources/             #    indicvoices_r · indictts · shrutilipi ·
│   │   │                        #    emilia · libritts_r · our_calls
│   │   ├── pipeline/            #    resample · loudness · transcript clean · dedupe ·
│   │   │                        #    speaker meta · manifest build
│   │   ├── manifests/           #    JSONL tracked in git; audio is not
│   │   └── corpus_export.py     # ★  WHERE consent_to_train — enforced, not remembered
│   ├── training/
│   │   ├── tts/lane_a/          #    small non-AR, preset voices, from scratch
│   │   ├── tts/lane_b/          #    reference-conditioned (cloning) — incl. Qwen3-TTS FT
│   │   └── stt/
│   └── notebooks/               #    exploration only; never a dependency
│
├── bench/                       # ── EVAL — decides every model swap ──
│   ├── conformance/             # ★  parametrised over the providers registry:
│   │                            #    chunk ordering · TTFB · cancel-mid-stream (barge-in)
│   │                            #    · language rejection · caps honesty · malformed input
│   ├── latency/                 #    per-hop harness + recorded-call replay driver
│   ├── datasets/hinglish/       #    300+ utterances, ≥30 min per language per condition
│   ├── stt_eval/                #    WER/CER on YOUR real-call set + bootstrap CIs
│   ├── tts_eval/                #    TTFB · audio-ms · UTMOS · ASR-intelligibility ·
│   │                            #    speaker similarity (SIM-o) for cloned voices
│   └── reports/                 #    committed per run — your quality changelog
│
├── deploy/
│   ├── docker/                  #    Dockerfile.{gateway,agent,api,worker,tts,stt} (Linux/CUDA)
│   ├── compose/                 #    dev.yml (infra only) · gpu-box.yml (full stack)
│   ├── seeds/                   #    agent config fixtures — imported into the DB, not read at runtime
│   ├── secrets/                 #    sops+age encrypted
│   └── runbooks/                #    "TTS box down" · "swap a model version" · "drain a deploy"
│
└── docs/
    ├── architecture.md          #    this document, kept current
    ├── adr/                     #    0001-pipecat-over-livekit · 0002-separate-model-servers ·
    │                            #    0003-db-is-config-authority · 0004-sentence-chunking ·
    │                            #    0005-two-model-tts-fleet
    ├── latency-budget.md
    ├── data-consent.md          #    call audio → training corpus
    └── voice-consent.md         #    cloned-voice consent, disclosure, tier policy
```

### 4.1 Boundary rules (a pre-commit grep, not CI machinery)

A folder structure is only worth as much as the rules about what may import what. Each of these prevents a specific future rewrite.

- `services/*`, `bench/*`, `research/*` may import `packages/*`. **Never the reverse.**
- **Service → service imports are forbidden.** Cross-plane data moves over HTTP (`api/routers/internal`) or through `packages/gotiny-db`. This is why the schema is a package.
- `services/agent` and `services/gateway` may **not** import a model library (`torch`, `transformers`, `nemo`, `onnxruntime`). Model clients live in `packages/gotiny-providers`; weights live in `services/{tts,stt}/backends`.
- **Nothing** in `services/` or `apps/` may import `research/`.
- `bench/conformance` imports `gotiny-providers` only — so it can test providers that don't exist yet.
- Only `services/api` and `services/worker` open a DB connection. The media plane never does.

### 4.2 Why the boundaries fall exactly there

| Boundary | The rewrite it prevents |
|---|---|
| `gotiny-providers` as a package, not folders inside `services/agent` | the conformance suite can't reach the adapters it exists to test |
| `gotiny-db` as a package, not `api/db/` | the agent has to import another service to write a turn row |
| `services/worker` separate from `api` | voice enrollment / recording post-processing block HTTP requests, or get done inline in the media plane |
| `services/gateway` separate from `agent` | no owner for signaling, warm pool, concurrency cap or drain — discovered under load |
| `gotiny.tts.services.routing` | the two-model fleet (preset vs cloned) gets hardcoded into the pipeline |
| `research/` unreachable from `services/` | torch and nemo end up in your agent's runtime image |
| `deploy/seeds/` instead of `personas/` in the agent image | three sources of truth for agent config; "prompt changes need no deploy" becomes false |

### 4.3 Conventions

- **Provider ids:** `name@semver` (`indicf5@0.3`, `gotiny-tts@0.1`), written on every `turn` row.
- **Voice ids:** foreign keys to the `voice` table. Resolution to reference audio is the TTS server's job.
- **Wire routes:** `/v1/tts:stream`. Version in the path, no negotiation machinery — one repo, one consumer. Revisit when there's an external API customer.
- **Agent config:** DB is authoritative. `deploy/seeds/*.yaml` is an import fixture. Tool *code* lives in the image, referenced by name from config.

## 5. What actually gets built when

Everything not listed is an empty directory with a one-line README saying what will live there — cheap, and it stops you inventing a new home under pressure.

| | Real code | Explicitly not yet |
|---|---|---|
| **Week 1** | `gotiny-providers` (registry + wire schemas + Pipecat service subclasses) · `gotiny-core` · `services/gateway` (signaling + warm pool + cap) · `services/agent` (bot, pipeline, smallwebrtc) · `services/tts`+`services/stt` as **host uvicorn processes** · `bench/conformance` · `apps/console` playground · repo tooling | DB, dashboard, auth, org tables |
| **Week 2** | `gotiny-db` + Alembic · `api` (`internal/` turn ingest, calls, agents) · `agent/telemetry.py` (spans + consumption) · `agent/disclosure.py` + the `ai_disclosure` field · `bench/latency` · `just cost` and `just latency` printing markdown from SQL | a console latency dashboard (a CLI query answers the same question); voice enrollment |
| **Week 3** | `gotiny-audio` · `research/data/{sources,pipeline}` · `bench/datasets/hinglish` (300+) · `stt_eval` + `tts_eval` with CIs and SIM-o · **Qwen3-TTS added as a bench baseline** · **build the STT container now** (pinned NeMo fork is a day of work, and week 3's bench depends on it) · `agent/recording.py` | training, terraform |
| **Week 4** | `deploy/docker` + `compose/gpu-box.yml` on the rented GPU · `services/worker` + pgmq (recording post-process) · Pipecat OTel → one collector · playground behind a password · sops secrets | telephony, multi-tenancy, voice cloning |
| **Phase 1** | `agent/transports/` telephony · `api/routers/webhooks` · real auth + `org`/`user`/`api_key` · console call log + config editor · dialer/campaigns · **Tier B voice cloning: `voices` router, `voice_enrollment` job, consent capture, `docs/voice-consent.md`** · terraform | Tier C self-serve cloning |
| **Phase 2** | `research/training/tts/lane_{a,b}` · `services/tts/backends/gotiny_v0.py` · `providers/tts/gotiny_tts_http.py` · `gotiny.tts.services.routing` gains the real fleet split — **zero changes to `agent/pipeline.py`** | — |

The Phase 2 row is the test of this design. If training your own TTS requires touching the pipeline, the seam failed.

---

## 6. Open decisions, deliberately deferred

| Decision | Trigger | Notes |
|---|---|---|
| LiveKit SIP vs Pipecat + Twilio/Exotel | first customer needing a number | LiveKit's native SIP + phone numbers is the strongest case for switching orchestration; `transports/` keeps the cost at days |
| WS vs gRPC to model servers | if WS framing appears in the TTFB trace | start WS — simpler, Python-native |
| Auth vendor | first customer with >1 user | both fine; don't build it |
| STT: IndicConformer vs whisper-large-v3 | week 3 bench on 300+ utterances with CIs | commit the report either way |
| **Own-TTS: from scratch vs fine-tune** | Phase 2 kickoff | Run it as a bench-off, not a preference. Lane A from scratch (Kokoro/StyleTTS2, Matcha/flow-matching and VITS/VAE-adversarial are *three distinct families*, not one lineage — pick one) vs **fine-tuning Qwen3-TTS-0.6B-Base on IndicVoices-R**, which may be cheaper *and* better. Test specifically for Indic prosody bleed; issue #323 shows 7 hrs single-speaker is nowhere near enough. Written ADR either way |
| **Does the fleet stay two models?** | when Tier B cloning has real usage | Lane A can't clone. If preset voices carry ≥90% of minutes, the two-model fleet is permanent and becomes a pricing tier; if not, Lane B absorbs everything and Lane A was wasted work |
| pgvector vs a search service | when transcript search gets slow | pgvector on the existing Postgres almost certainly wins at your scale |

---

## 7. The first six things to create

1. `packages/gotiny-providers` — registry, wire schemas, and Pipecat service subclasses wrapping the extras Pipecat already ships. An afternoon; saves a quarter.
2. `bench/conformance/` — parametrised over the registry, including cancel-mid-stream. Barge-in is a *contract* requirement, not a feature.
3. `services/gateway` + `services/agent` + host-run `tts`/`stt` — Friday's spoken conversation, over the same HTTP path you'll run in production.
4. `packages/gotiny-db` + `turn` with timing **and** consumption columns — instrumentation before optimisation, costing before pricing.
5. ADRs `0001`–`0004` (Pipecat over LiveKit · separate model servers · DB as config authority · sentence-level chunking). Write down why, so month 4 doesn't relitigate it.
6. `docs/data-consent.md` + the consent clause in your contract template — the flywheel is legally load-bearing. Add `ai_disclosure` to the agent config in the same sitting; it costs a line now and a migration-plus-renegotiation later.

---

*Version claims verified Aug 2026: [pipecat-ai on PyPI](https://pypi.org/project/pipecat-ai/) (1.7.0, 1 Aug 2026, Python ≥3.11) · [Pipecat docs](https://docs.pipecat.ai/overview/introduction) · [SmallWebRTC transport](https://docs.pipecat.ai/server/services/transport/small-webrtc) · [Pipecat vs LiveKit 2026](https://www.evalgent.com/blog/pipecat-vs-livekit) · [ai4bharat/IndicF5](https://huggingface.co/ai4bharat/IndicF5) · [ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large](https://huggingface.co/ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large) · [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) · [AI4Bharat model stack](https://www.indiaaipulse.com/en/news/ai4bharat-expands-indic-ai-model-stack) · [Next.js 16.3](https://nextjs.org/blog/next-16-3) · [pgmq](https://github.com/pgmq/pgmq)*
