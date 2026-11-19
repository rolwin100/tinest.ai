import { developers } from "@/content/site";
import { CodeTabs, type Snippet } from "@/components/code-tabs";
import { CheckIcon } from "@/components/ui/icons";

/**
 * These mirror packages/gotiny-providers/src/gotiny/providers/wire.py.
 * If the wire contract changes, change them here in the same commit — a docs
 * snippet that lies is worse than no snippet.
 */
const snippets: Array<Snippet> = [
  {
    label: "Node",
    language: "javascript",
    code: `const ws = new WebSocket("wss://api.gotiny.ai/v1/tts:stream", {
  headers: { Authorization: "Bearer " + process.env.GOTINY_API_KEY },
});

ws.addEventListener("open", () => {
  ws.send(JSON.stringify({
    request_id: crypto.randomUUID(),
    text: "Your appointment is confirmed for Tuesday at four.",
    voice_id: "en-female-01",
    language: "en-US",
    sample_rate: 24000,
    speed: 1.0,
  }));
});

ws.addEventListener("message", (event) => {
  if (typeof event.data === "string") {
    const trailer = JSON.parse(event.data);   // { done, ttfb_ms, audio_ms, chars }
    console.log("first byte in", trailer.ttfb_ms, "ms");
    return;
  }
  speaker.write(Buffer.from(event.data));     // PCM s16le mono, sentence-chunked
});`,
  },
  {
    label: "Python",
    language: "python",
    code: `import json, uuid, websockets

async with websockets.connect(
    "wss://api.gotiny.ai/v1/tts:stream",
    additional_headers={"Authorization": f"Bearer {API_KEY}"},
) as ws:
    await ws.send(json.dumps({
        "request_id": str(uuid.uuid4()),
        "text": "Your appointment is confirmed for Tuesday at four.",
        "voice_id": "en-female-01",
        "language": "en-US",
        "sample_rate": 24000,
    }))

    async for frame in ws:
        if isinstance(frame, bytes):
            stream.write(frame)               # PCM s16le mono
        else:
            trailer = json.loads(frame)       # done, ttfb_ms, audio_ms, chars
            break`,
  },
  {
    label: "cURL",
    language: "bash",
    code: `# Discover what this region can do before you hardcode anything.
curl https://api.gotiny.ai/v1/caps \\
  -H "Authorization: Bearer $GOTINY_API_KEY"

# {
#   "wire": "v1",
#   "backends": [
#     { "name": "kokoro-onnx@1.0", "streaming": true, "supports_cloning": false },
#     { "name": "gotiny-tts@0.1",  "streaming": true, "supports_cloning": true  }
#   ],
#   "voices": [ { "voice_id": "en-female-01", "language": "en-US", ... } ]
# }`,
  },
];

export function Developers() {
  return (
    <section id="developers" className="scroll-mt-20 border-t border-border py-24">
      <div className="shell grid items-start gap-12 lg:grid-cols-2 lg:gap-16">
        <div className="lg:sticky lg:top-28">
          <p className="text-overline text-accent">
            {developers.eyebrow}
          </p>
          <h2 className="text-section mt-3 text-balance">{developers.title}</h2>
          <p className="mt-4 text-base leading-relaxed text-pretty text-fg-muted">
            {developers.sub}
          </p>

          <ul className="mt-8 space-y-4">
            {developers.points.map((point) => (
              <li key={point} className="flex gap-3">
                <CheckIcon className="mt-0.5 size-4 shrink-0 text-accent" />
                <span className="text-sm leading-relaxed text-fg-muted">{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <CodeTabs snippets={snippets} />
      </div>
    </section>
  );
}
