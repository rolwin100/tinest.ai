# apps/site — gotiny.ai marketing site

Next.js 16 (App Router) + Tailwind v4. Separate from `apps/studio`: the studio is
the product, this is the front door. It shares nothing but the brand, which is
deliberate — a marketing page should be deployable to a CDN with no server, no
database and no model in the request path.

## Run it

```bash
cd apps/site
pnpm install
pnpm dev            # http://localhost:3001
```

Port 3001 so it can run alongside the studio on 3000.

## Where the content lives

**`src/content/site.ts` is the site.** Every headline, feature blurb, price and
stat is there; the components under `src/components` are layout only. Change
copy there and nothing else needs touching.

Anything marked `PLACEHOLDER` in that file is a number or claim that has not
been measured or decided yet — latency figures, uptime, pricing. Replace them
with real numbers from `bench/reports/` before this is public.

`src/content/demo.json` is shared between the site and the render script: the
demo lines (per language) and the voices shown in the hero picker and the voice
library. Add a voice there and both pick it up.

Each prompt is `{ label, text }`. The label is what the chip says — "Support
call", "Brand read" — because numbering the lines reads as carousel pagination
and promises rotation the player does not do. Clip ids are still
`voiceId:index`, so relabelling or rewording a line does not invalidate samples
you have already rendered; only reordering does.

## The demo audio

The hero player and the voice library play **pre-rendered** clips, not live
synthesis. Reasons: no GPU in the path of a first impression, no rate limiting
to build, and the whole site stays statically hostable.

The clips are produced from the real TTS server over the real wire protocol:

```bash
just tts                     # terminal 1 — server on :8081
cd apps/site
pnpm render:samples          # terminal 2
```

That writes `public/samples/*.wav` plus `public/samples/manifest.json`. The wav
files are gitignored (regenerate them); the manifest is committed so the build
knows what exists. Until you run it, the players render with a disabled play
button and a note — which is the intended state, not a bug.

Point at a different server with `GOTINY_TTS_URL=http://host:port`. Set
`GOTINY_DEBUG=1` to print negotiated WebSocket extensions and a line per audio
frame as it arrives.

### Why this script uses `ws`, not the built-in WebSocket

uvicorn negotiates `permessage-deflate` by default, and Node's built-in global
`WebSocket` (undici) advertises support for that extension during the
handshake but doesn't actually implement frame decompression — it aborts
mid-stream (close code 1006) on the first compressed binary frame. Browsers
cope, so `apps/studio` never saw it, but here it silently truncated every clip
to its first sentence, or produced nothing at all for single-sentence lines,
while the server logged success the whole time.

The fix is on this end, not the server's: the script uses the `ws` package
(a real permessage-deflate implementation, compression on by default) instead
of the global `WebSocket`. The server keeps compression on — it was never the
problem. If clips come out short again, run with `GOTINY_DEBUG=1` and check
the `negotiated extensions:` line first; `permessage-deflate` should be listed.

The script now resolves on the wire protocol's trailer rather than on socket
close — the trailer is the contract's terminator and arrives after the last
audio frame — and warns when the trailer's `audio_ms` disagrees with the
captured PCM duration. That check is what turns a silently truncated clip into
a visible failure.

## Theming

Light by default, dark behind the toggle in the nav. Choice is stored in
`localStorage` and applied before paint, so there is no flash. Both palettes are
defined completely in `src/app/globals.css`; no component knows which one it is
rendering in.

The tokens are not taste — they are measured. See below.

## design/ — where the look came from

`design/design-dna.json` is a structured design-system spec distilled from
elevenlabs.io and fish.audio, following the Design DNA method in
`.claude/skills/web-clone/references/design-dna.md`. That method is explicitly
the *visual-reproduction* branch of the skill, not the byte-faithful one: style
is inherited, nothing is copied. No markup, CSS, asset, wordmark or line of copy
from either site is in this repo.

`design/RECON/*.json` holds the raw measurements behind it — computed styles
sampled across each homepage's visible DOM on 11 Sept 2026.

Three findings drove most of the tokens, and they are the ones an
eyeball-imitation gets wrong:

1. **The neutral ramp is warm, not gray.** Both sites sit on an off-white with a
   beige cast (`#FDFCFC`, `#FAF8F5`) and every surface above it keeps that cast.
   Cool grays are what make this genre read as cheap.
2. **Display type is light.** ElevenLabs sets its 48px headline at weight **300**;
   fish.audio at 400. Neither goes bold. Scale and whitespace carry the
   hierarchy, not weight. Body text tracks slightly *open* (+0.01em) while only
   display tracks tight (−0.02em).
3. **Separation is a hairline, not a shadow.** 1px warm-gray borders and a change
   of background tone. The only element here with real elevation is the hero
   demo card.

Structurally: the hero is **asymmetric** — headline left, supporting paragraph
floated right — on both sites. Buttons are pills (9999px was ElevenLabs' most
common radius, 167 uses). Content maxes at ~1150px. Motion is
`cubic-bezier(0.4, 0, 0.2, 1)` at 150ms for state and
`cubic-bezier(0.22, 1, 0.36, 1)` for entrances. Neither site uses canvas, WebGL,
particles, parallax or cursor effects — measured, not assumed. Don't add any.

The accent is fish.audio's teal. ElevenLabs uses no chromatic accent at all, so
accent coverage stays under ~2% of the page and the primary button is near-black,
not coloured. To match `apps/studio` instead, change `--accent` in `globals.css`
to the studio's violet — it is one token.

## Voice orbs

Each voice has a gradient sphere derived from its `voice_id`
(`src/components/orb.tsx`), so it looks like itself in the hero, the voice pills
and the library cards — nothing to commission, nothing to download.

The palette is a narrow analogous triad, three hues within roughly 80°. That
narrowness is deliberate: it keeps the sphere reading as one material catching
the light rather than as a beach ball.

**Motion moves the palette, it does not extend it.** Two conic washes painted
from those same three hues counter-rotate over the static radial body at
different speeds; where they cross, the overlay blend brightens and the surface
churns. Counter-rotation is the trick — one rotating layer reads as a wheel
turning, two read as fluid. A still frame of the animated orb is the same orb
you would get with motion off.

Motion is opt-in per instance via `motion`:

- `still` (default) — for the small, repeated orbs in pills and cards
- `idle` — slow churn; the hero orb at rest
- `live` — faster churn plus a breathing glow, while audio plays

That split is not decoration: a dozen blurred, animating orbs on one page is
real compositing work, so only the one you are looking at moves. Each orb also
takes a negative animation delay from its seed, so two on screen are never in
phase. `prefers-reduced-motion` stops all of it.

Speed is the `speed` constant in `orb.tsx`: seconds per full rotation of the
leading wash (12s idle, 5s live), with the trailing wash at 1.55x that. The beat
between the two is what reads as churn, so keep the ratio when you change them.

`blur` scales with the rendered size and is passed by the caller — roughly 10%
of the diameter — because the component cannot measure itself.

The orbs are the only saturated colour on the page, which is why every control
around them is near-black.

## Code highlighting

`src/lib/highlight.ts` is a small tokenizer for the three languages the
Developers section shows. Not Shiki or Prism: the snippets are fixed, short and
ours, and a grammar engine would add a dependency and a build step for six
hundred characters of code. If arbitrary code ever needs highlighting — a docs
site — swap in Shiki at build time and delete the file.

The palette (`--syntax-*` in `globals.css`) is deliberately near-monochrome with
three low-chroma hues. Both references are almost colourless; a rainbow code
block would be the loudest thing on the page. Function names carry no hue at all
— they read as emphasis.

## What is not here yet

- Docs. The `Developers` section links to an anchor; point it at real docs when
  they exist.
- Sign-in / sign-up. Nav and CTAs point at `localhost:3000` (the studio) as a
  stand-in.
- An OG image. Add `src/app/opengraph-image.tsx` when the brand is settled.
- A display typeface. Both references license a bespoke face (Waldenburg, Onest).
  Inter Light at weight 300 is the honest stand-in; swapping `--font-sans` for a
  real display face is the single biggest upgrade available to this page.
