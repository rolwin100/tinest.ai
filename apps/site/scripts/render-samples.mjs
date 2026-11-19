#!/usr/bin/env node
/**
 * Render the marketing site's demo clips from the real TTS server.
 *
 * The site never calls the model at request time — a landing page should not
 * put a GPU between a stranger and their first impression. Instead this script
 * speaks the same wire protocol the studio does (packages/gotiny-providers
 * wire.py), writes one WAV per voice-and-line, and emits a manifest the page
 * reads at build time.
 *
 *   just tts                  # in one terminal, server on :8081
 *   pnpm render:samples       # in another
 *
 * Override the server with GOTINY_TTS_URL.
 *
 * Uses the `ws` package rather than Node's built-in WebSocket. Node's global
 * WebSocket (undici) advertises permessage-deflate support in the handshake
 * but does not actually implement frame decompression, so once uvicorn
 * negotiates the extension (its default), every compressed binary frame
 * fails to decode and the socket aborts mid-stream — close code 1006, no
 * trailer, whatever text happened to be in the first uncompressed-enough
 * frame. `ws` implements RFC 7692 properly and keeps compression on by
 * default (`perMessageDeflate: true`), which is what actually fixes this:
 * the server was never the problem, the client's decoder was.
 */

import { mkdir, writeFile, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import WebSocket from "ws";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const outDir = join(root, "public", "samples");

const HTTP_BASE = process.env.GOTINY_TTS_URL ?? "http://127.0.0.1:8081";
const WS_BASE = HTTP_BASE.replace(/^http/, "ws");
const SAMPLE_RATE = 24_000;

/** PCM s16le mono -> a .wav file the browser will play without ceremony. */
function wav(pcm, sampleRate) {
  const header = Buffer.alloc(44);
  header.write("RIFF", 0);
  header.writeUInt32LE(36 + pcm.length, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16); // PCM chunk size
  header.writeUInt16LE(1, 20); // format: PCM
  header.writeUInt16LE(1, 22); // channels: mono
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(sampleRate * 2, 28); // byte rate
  header.writeUInt16LE(2, 32); // block align
  header.writeUInt16LE(16, 34); // bits per sample
  header.write("data", 36);
  header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
}

function synthesise({ text, voiceId, language }) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`${WS_BASE}/v1/tts:stream`);

    const chunks = [];
    const t0 = Date.now();
    const since = () => `${((Date.now() - t0) / 1000).toFixed(1)}s`;
    let settled = false;
    const timer = setTimeout(() => {
      ws.terminate();
      finish(() => reject(new Error("timed out after 120s")));
    }, 120_000);

    function finish(fn) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      fn();
    }

    ws.on("open", () => {
      if (process.env.GOTINY_DEBUG) {
        const negotiated = Object.keys(ws.extensions ?? {}).join(", ");
        console.log(`\n      negotiated extensions: ${negotiated || "(none)"}`);
      }
      ws.send(
        JSON.stringify({
          request_id: randomUUID(),
          text,
          voice_id: voiceId,
          language,
          sample_rate: SAMPLE_RATE,
          speed: 1.0,
        }),
      );
    });

    ws.on("message", (data, isBinary) => {
      if (!isBinary) {
        const frame = JSON.parse(data.toString("utf8"));
        if (frame.error) {
          ws.close();
          finish(() => reject(new Error(`${frame.kind}: ${frame.error}`)));
          return;
        }

        // The trailer terminates the stream — that is the contract, and it is
        // what the studio client waits for too. Waiting for the socket to close
        // instead means racing the server's teardown against the delivery of
        // the last audio frame, and losing that race silently.
        ws.close();
        finish(() => resolve({ pcm: Buffer.concat(chunks), trailer: frame, frames: chunks.length }));
        return;
      }

      // `ws` delivers each message as its own freshly-allocated Buffer, so
      // there's no receive-buffer aliasing to guard against here.
      chunks.push(data);
      if (process.env.GOTINY_DEBUG) {
        console.log(`\n      frame ${chunks.length}: ${data.byteLength} bytes at ${since()}`);
      }
    });

    ws.on("error", (error) => {
      finish(() => reject(new Error(`socket error after ${since()} — ${error.message}`)));
    });

    ws.on("close", (code, reason) => {
      // Only reached when the server closed without a trailer. The close code
      // is the useful part: 1000 is a deliberate hang-up, 1006 an abnormal
      // drop (process died, or the peer never sent a close frame), 1011 an
      // unhandled server error.
      const reasonText = reason?.length ? ` "${reason.toString("utf8")}"` : "";
      const why = `code ${code}${reasonText} after ${since()}`;
      finish(() =>
        reject(
          new Error(
            chunks.length === 0
              ? `closed without audio or trailer — ${why}`
              : `closed after ${chunks.length} frame(s) without a trailer — ${why}`,
          ),
        ),
      );
    });
  });
}

async function main() {
  const demo = JSON.parse(
    await readFile(join(root, "src", "content", "demo.json"), "utf8"),
  );

  await mkdir(outDir, { recursive: true });

  const clips = [];
  const failures = [];

  for (const voice of demo.voices) {
    const prompts = demo.prompts[voice.language] ?? demo.prompts["en-US"];

    for (const [index, prompt] of prompts.entries()) {
      const name = `${voice.id}-${index}.wav`;
      process.stdout.write(`  ${voice.name.padEnd(9)} ${prompt.label.padEnd(12)} … `);

      try {
        const { pcm, trailer, frames } = await synthesise({
          text: prompt.text,
          voiceId: voice.id,
          language: voice.language,
        });

        await writeFile(join(outDir, name), wav(pcm, SAMPLE_RATE));

        const durationMs = trailer?.audio_ms ?? (pcm.length / 2 / SAMPLE_RATE) * 1000;
        clips.push({
          id: `${voice.id}:${index}`,
          voiceId: voice.id,
          promptIndex: index,
          src: `/samples/${name}`,
          durationMs: Math.round(durationMs),
        });

        const ttfb = trailer?.ttfb_ms ? `${Math.round(trailer.ttfb_ms)}ms first byte` : "";
        const capturedMs = (pcm.length / 2 / SAMPLE_RATE) * 1000;

        // If these disagree, the server sent audio this script did not keep —
        // which is the failure mode that silently produced half-sentences.
        const drift = Math.abs(capturedMs - (trailer?.audio_ms ?? capturedMs));
        const warn = drift > 50
          ? `  ⚠ server reported ${Math.round(trailer.audio_ms)}ms, captured ${Math.round(capturedMs)}ms`
          : "";

        console.log(`ok  ${(durationMs / 1000).toFixed(1)}s  ${frames} frame(s)  ${ttfb}${warn}`);
      } catch (error) {
        failures.push(`${voice.id} / ${prompt.label}: ${error.message}`);
        console.log(`failed — ${error.message}`);
      }

      // Brief pause so the server can release the session before the next request.
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }

  await writeFile(
    join(outDir, "manifest.json"),
    `${JSON.stringify({ generatedAt: new Date().toISOString(), clips }, null, 2)}\n`,
  );

  console.log(`\n${clips.length} clip(s) written to public/samples/`);
  if (failures.length > 0) {
    console.log(`${failures.length} failed:`);
    for (const failure of failures) console.log(`  - ${failure}`);
    process.exitCode = 1;
  }
}

console.log(`Rendering demo clips from ${HTTP_BASE}\n`);
await main();
