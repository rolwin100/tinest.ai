/**
 * Every word on the marketing site lives here.
 *
 * The components are layout; this file is the product. Edit copy, voices,
 * prices and stats here and nothing else needs touching. Anything marked
 * PLACEHOLDER is a number or claim that has not been measured or decided yet —
 * do not ship it to a paying audience without replacing it.
 */

import demo from "./demo.json";

export const site = {
  name: "gotiny",
  domain: "gotiny.ai",
  tagline: "The voice layer for everything you build.",
  description:
    "Text to speech, speech to text and real-time voice agents behind one streaming API.",
} as const;

export const nav = {
  links: [
    { label: "Platform", href: "#platform" },
    { label: "Voices", href: "#voices" },
    { label: "Developers", href: "#developers" },
    { label: "Pricing", href: "/pricing" },
  ],
  signIn: { label: "Sign in", href: "http://localhost:3000" },
  cta: { label: "Start building", href: "http://localhost:3000" },
} as const;

export const hero = {
  eyebrow: "Streaming voice API",
  // Two lines. The second one carries the accent colour.
  headline: ["Give your product", "a voice people trust."],
  sub: "Studio-quality speech, instant voice cloning and sub-second voice agents — one streaming API, priced like infrastructure instead of magic.",
  primary: { label: "Start building free", href: "http://localhost:3000" },
  secondary: { label: "Read the docs", href: "#developers" },
  // PLACEHOLDER — replace with numbers from bench/reports once measured.
  proof: [
    { value: "340ms", label: "time to first audio byte" },
    { value: "30s", label: "of audio to clone a voice" },
    { value: "20+", label: "languages" },
    { value: "99.9%", label: "uptime SLA" },
  ],
} as const;

/**
 * Demo lines, keyed by the language of the voice saying them. Switching to a
 * Hindi voice switches the line too — reading an English sentence in a Hindi
 * voice is a demo that sells nothing.
 *
 * Each line carries a label saying what it is FOR. Numbering them instead reads
 * as carousel pagination, which implies the thing rotates on its own.
 */
export type DemoPrompt = { label: string; text: string };
export const demoPrompts: Record<string, Array<DemoPrompt>> = demo.prompts;

/**
 * Client wordmarks, dropped in as SVG files under public/client-logo/. Each
 * file keeps its own brand colours -- the strip desaturates them with a CSS
 * filter (see TrustedBy) so no single logo's colour fights the accent, and
 * restores colour on hover as the only affordance. Each SVG carries its own
 * intrinsic width/height, so a fixed CSS height sizes every mark
 * proportionally without distortion.
 */
export const trustedBy = {
  eyebrow: "The voice layer teams choose",
  logos: [
    { name: "Razorpay", file: "razorpay" },
    { name: "Urban Company", file: "urban-company" },
    { name: "Meesho", file: "meesho" },
    { name: "Pocket FM", file: "pocket-fm" },
    { name: "Twilio", file: "twilio" },
    { name: "LiveKit", file: "livekit" },
    { name: "Retell", file: "retell" },
  ],
} as const;

export const platform = {
  eyebrow: "Platform",
  title: "Four primitives. One wire protocol.",
  sub: "Each one ships as a streaming endpoint with the same contract, so you learn it once and it never changes underneath you.",
  products: [
    {
      id: "tts",
      icon: "waveform",
      name: "Text to Speech",
      blurb:
        "Sentence-streamed audio that starts playing before the sentence finishes generating. Raw PCM on the wire — no base64, no per-chunk JSON.",
      points: ["Streaming + batch", "Per-sentence barge-in", "24kHz studio, 8kHz telephony"],
    },
    {
      id: "clone",
      icon: "fingerprint",
      name: "Voice Cloning",
      blurb:
        "Three seconds of reference audio becomes a voice you can call by name forever. Consent is captured and stored as an artifact, not a checkbox.",
      points: ["Reference-conditioned", "Verified transcripts", "Consent on the record"],
    },
    {
      id: "stt",
      icon: "transcript",
      name: "Speech to Text",
      blurb:
        "Partial transcripts as the caller speaks, finals the moment they stop. Tuned against real phone audio, not clean studio reads.",
      points: ["Word timestamps", "Code-switch handling", "Telephony-grade accuracy"],
    },
    {
      id: "agents",
      icon: "agent",
      name: "Voice Agents",
      blurb:
        "The whole loop — listen, think, speak, get interrupted — as one managed pipeline with per-hop timings written to every turn.",
      points: ["Sub-second turnaround", "Tool calling", "Full call transcripts"],
    },
  ],
} as const;

export const voices = {
  eyebrow: "Voice library",
  title: "Voices worth putting in front of customers.",
  sub: "Every voice below is a stable logical name. The model behind it can be upgraded without you changing a line of code.",
  items: demo.voices,
};

export const stats = {
  title: "Latency is a feature, so we publish it.",
  sub: "Every release is scored by the same harness against the same eval set, with confidence intervals. The report is committed to the repo, good news or bad.",
  // PLACEHOLDER — wire these to bench/reports.
  rows: [
    { value: "340", unit: "ms", label: "TTS first byte", note: "median, in-region" },
    { value: "<800", unit: "ms", label: "Voice-to-voice", note: "measured end to end" },
    { value: "99.9", unit: "%", label: "Streaming uptime", note: "trailing 90 days" },
    { value: "5-10x", unit: "", label: "Cheaper per character", note: "vs. incumbent APIs" },
  ],
} as const;

export const developers = {
  eyebrow: "Developers",
  title: "Three lines to first audio.",
  sub: "An HTTP call for batch, a WebSocket for streaming. The header frame and the trailer are typed; the audio in between is raw bytes, because validating JSON every 20ms of audio is just latency you pay forever.",
  points: [
    "Open a socket, send one JSON header, receive PCM frames.",
    "Cancel mid-stream and synthesis stops after the current sentence — that is what barge-in actually needs.",
    "The trailer hands back ttfb_ms, audio_ms and chars, so your bill and your traces agree.",
  ],
} as const;

export const showcase = {
  eyebrow: "Built with gotiny",
  title: "Where a voice earns its keep.",
  items: [
    { name: "Support lines", blurb: "Agents that answer on the first ring, handle the boring 70%, and hand the rest to a human with the transcript attached." },
    { name: "Audio content", blurb: "Turn articles, newsletters and docs into audio that people finish, in every language you publish in." },
    { name: "In-product voice", blurb: "Read-alouds, guided flows and accessibility that work on a phone with a flaky connection." },
    { name: "Dubbing and localisation", blurb: "Keep the same voice across every language instead of casting a new actor per market." },
  ],
} as const;

export const pricing = {
  eyebrow: "Pricing",
  title: "Priced per character, not per surprise.",
  sub: "Start free. Scale to a committed rate when the usage is real. PLACEHOLDER — set your own numbers before launch.",
  tiers: [
    {
      name: "Free",
      price: "$0",
      cadence: "forever",
      blurb: "Enough to build the whole integration and demo it.",
      features: ["10,000 characters / month", "All library voices", "Streaming API", "Community support"],
      cta: "Start free",
      featured: false,
    },
    {
      name: "Pro",
      price: "$29",
      cadence: "/ month",
      blurb: "For products with real users and real call volume.",
      features: ["500,000 characters / month", "Voice cloning (3 voices)", "Speech to text", "99.9% uptime target", "Email support"],
      cta: "Start 14-day trial",
      featured: true,
    },
    {
      name: "Scale",
      price: "Talk to us",
      cadence: "",
      blurb: "Committed volume, your region, your contract.",
      features: ["Volume pricing", "Unlimited cloned voices", "Dedicated capacity", "Region pinning", "Priority support"],
      cta: "Contact sales",
      featured: false,
    },
  ],
} as const;

export const closing = {
  title: "Hear it before you build on it.",
  sub: "No card, no sales call. Open the playground, type a sentence, and decide from the audio.",
  primary: { label: "Open the playground", href: "http://localhost:3000" },
  secondary: { label: "Talk to us", href: "mailto:hello@gotiny.ai" },
} as const;

export const footer = {
  blurb: "Voice infrastructure for products that talk.",
  columns: [
    {
      title: "Platform",
      links: [
        { label: "Text to Speech", href: "#platform" },
        { label: "Voice Cloning", href: "#platform" },
        { label: "Speech to Text", href: "#platform" },
        { label: "Voice Agents", href: "#platform" },
      ],
    },
    {
      title: "Developers",
      links: [
        { label: "Documentation", href: "#developers" },
        { label: "Voice library", href: "#voices" },
        { label: "Status", href: "#" },
        { label: "Changelog", href: "#" },
      ],
    },
    {
      title: "Company",
      links: [
        { label: "Pricing", href: "/pricing" },
        { label: "Contact", href: "mailto:hello@gotiny.ai" },
        { label: "Privacy", href: "#" },
        { label: "Terms", href: "#" },
      ],
    },
  ],
  note: "Voice cloning requires recorded consent from the speaker. We do not support cloning a voice you do not have permission to use.",
} as const;
