# gotiny.ai — task runner.  `just` with no args lists everything.
default:
    @just --list

# ── setup ──
install:
    uv sync --all-packages --extra kokoro --extra whisper
    cp -n .env.example .env || true

# ── quality gates ──
lint:
    uv run ruff check .
    uv run ruff format --check .

fmt:
    uv run ruff format .
    uv run ruff check --fix .

types:
    uv run mypy packages

# The conformance suite: every provider must pass the SAME tests.
# Runs against the fakes always, and against the live TTS server if it is up.
conformance:
    uv run pytest bench/conformance -v

test: lint types conformance

# ── model servers (host processes: macOS Docker has no Metal/MPS) ──
# First run downloads ~340MB of Kokoro weights into ~/.cache/gotiny/kokoro.
# uvicorn negotiates permessage-deflate by default (ws_per_message_deflate=True).
# Node's built-in WebSocket (undici) advertises support for the extension but
# doesn't actually implement frame decompression, so it aborts mid-stream
# (close 1006) on the first compressed binary frame -- browsers cope, which is
# why apps/studio never saw this. Compression stays on here: the fix lives on
# the client, not the server -- see apps/site/scripts/render-samples.mjs,
# which uses the `ws` package (a real permessage-deflate implementation)
# instead of the global WebSocket.
tts:
    uv run uvicorn gotiny.tts.app:app --host 127.0.0.1 --port 8081 --reload

# Synthesise a line, measure first-byte latency, write out.wav. Needs `just tts`.
say text="नमस्ते। मैं आपकी मदद कर सकती हूँ।" voice="hi-female-01" lang="hi" rate="24000" speed="1.0":
    cd bench && uv run python -m latency.tts_probe \
        --text "{{text}}" --voice "{{voice}}" --language "{{lang}}" --rate {{rate}} \
        --speed {{speed}} --out ../out.wav

# STT server. First run downloads the Whisper model (~500MB for `small`).
stt:
    uv run uvicorn gotiny.stt.app:app --host 127.0.0.1 --port 8082 --reload

# Transcribe a wav. Needs `just stt` running.
hear wav="out.wav" lang="hi-en":
    cd bench && uv run python -m latency.stt_probe "../{{wav}}" --language "{{lang}}"

# Full loop: synthesise a line, then transcribe it back. Needs both servers.
roundtrip text="नमस्ते। मैं आपकी मदद कर सकती हूँ।":
    @just say "{{text}}"
    @just hear out.wav hi

# The front door. Needs `just tts`, `just stt` and ollama running.
gateway:
    uv run uvicorn gotiny.gateway.app:app --host 127.0.0.1 --port 8080 --reload

# Open the playground in a browser. Needs `just gateway`.
play:
    @open http://127.0.0.1:8080/ 2>/dev/null || echo "open http://127.0.0.1:8080/"

# What the gateway is doing right now: live calls, capacity, end-reason tally.
calls:
    @curl -sf http://127.0.0.1:8080/health 2>/dev/null | uv run python -m json.tool 2>/dev/null \
      || echo "no gateway on :8080 - start it with 'just gateway' (its own terminal has the traceback if it failed to boot)"

voices:
    curl -s http://127.0.0.1:8081/v1/caps | uv run python -m json.tool

# The studio (TanStack Start) on :3000. Needs `just tts` running for live synthesis.
studio:
    cd apps/studio && pnpm install && pnpm dev
