import type { CSSProperties } from "react";
import { hashSeed, mulberry32 } from "@/lib/seed";
import { cn } from "@/lib/cn";

/**
 * A voice's visual identity: a gradient sphere whose colours are derived from
 * its voice_id, so every voice looks like itself everywhere it appears and
 * nobody has to commission six illustrations.
 *
 * The palette is a narrow analogous triad — three hues within roughly 80° of
 * each other. That narrowness is the point: it keeps the sphere reading as one
 * material catching the light rather than as a beach ball.
 *
 * Motion does not add colours, it moves the ones already there. Two conic
 * washes counter-rotate over the base radial at different speeds; where they
 * cross, the overlay blend brightens and the surface appears to churn. Nothing
 * enters or leaves the palette, so a still frame of the animated orb is the
 * same orb as before.
 *
 * Four layers, no canvas and no library:
 *   1. an off-centre radial for the body and the light source (static — this
 *      is what fixes the orb's identity),
 *   2. two blurred conic washes, counter-rotating, overlay-blended,
 *   3. inset shadows for terminator and rim light.
 */
type OrbProps = {
  seed: string;
  className?: string;
  /**
   * "still" — no animation (default; use for small or repeated orbs)
   * "idle"  — slow churn, for a hero orb that should feel alive at rest
   * "live"  — faster churn plus a breathing glow, while audio plays
   */
  motion?: "still" | "idle" | "live";
  /**
   * Blur radius of the conic washes, in px. It has to scale with the rendered
   * size — 10px of blur on a 20px orb is just a smudge — and the component
   * cannot measure itself, so callers pass it. Roughly 10% of the diameter.
   */
  blur?: number;
};

/**
 * Hash collisions happen, and this one was visible: en-male-01 hashed to 162°,
 * a few degrees off en-female-01's 130°, so Aria and Michael read as the same
 * voice. Pinning the one that clashed is cheaper than re-colouring the set.
 * Add an entry here only when two orbs actually look alike.
 */
const HUE_OVERRIDES: Record<string, number> = {
  "en-male-01": 25,
};

export function Orb({
  seed,
  className,
  motion = "still",
  blur = 10,
}: OrbProps) {
  const rand = mulberry32(hashSeed(seed));

  // The hashed hue is consumed either way, so an override changes the colour
  // without shifting the spread, tilt and phase that follow it.
  const hashedHue = Math.floor(rand() * 360);
  const base = HUE_OVERRIDES[seed] ?? hashedHue;
  const spread = 38 + rand() * 34;
  const h1 = base;
  const h2 = (base + spread) % 360;
  const h3 = (base + spread * 2) % 360;
  const tilt = Math.floor(rand() * 360);

  const moving = motion !== "still";
  // Negative delays so two orbs on the same page are never in phase.
  const offset = -rand() * 20;
  // Seconds per full rotation of the leading wash; the trailing one runs 1.55x
  // slower, and the beat between them is what you actually read as churn.
  const speed = motion === "live" ? 5 : 12;

  const wash = (from: number) =>
    `conic-gradient(from ${from}deg,
      oklch(0.95 0.14 ${h2}) 0deg,
      oklch(0.45 0.16 ${h3}) 120deg,
      oklch(0.88 0.12 ${h1}) 240deg,
      oklch(0.95 0.14 ${h2}) 360deg)`;

  return (
    <div
      className={cn(
        "relative isolate aspect-square shrink-0 overflow-hidden rounded-full [clip-path:circle(50%)]",
        motion === "live" && "orb-live",
        className,
      )}
      style={
        {
          background: `radial-gradient(circle at 32% 26%,
            oklch(0.94 0.09 ${h1}) 0%,
            oklch(0.78 0.17 ${h2}) 34%,
            oklch(0.55 0.18 ${h3}) 72%,
            oklch(0.36 0.13 ${h3}) 100%)`,
          "--orb-glow": `oklch(0.62 0.18 ${h2} / 42%)`,
        } as CSSProperties
      }
      aria-hidden="true"
    >
      <div
        className={cn("absolute -inset-1/4 mix-blend-overlay", moving && "orb-spin")}
        style={
          {
            background: wash(tilt),
            filter: `blur(${blur}px)`,
            "--orb-dur": `${speed}s`,
            "--orb-delay": `${offset}s`,
          } as CSSProperties
        }
      />

      {/* Counter-rotating, slower and softer. This second pass is what turns a
          spin into a churn — one rotating layer just looks like a wheel. */}
      <div
        className={cn(
          "absolute -inset-1/4 opacity-60 mix-blend-overlay",
          moving && "orb-spin-reverse",
        )}
        style={
          {
            background: wash((tilt + 180) % 360),
            filter: `blur(${blur * 1.3}px)`,
            "--orb-dur": `${speed * 1.55}s`,
            "--orb-delay": `${offset * 0.6}s`,
          } as CSSProperties
        }
      />

      <div
        className="absolute inset-0 rounded-full"
        style={{
          boxShadow: `inset -${blur * 0.6}px -${blur}px ${blur * 2.2}px oklch(0.2 0.06 ${h3} / 45%),
                      inset ${blur * 0.5}px ${blur * 0.7}px ${blur * 1.6}px oklch(1 0 0 / 30%)`,
        }}
      />
    </div>
  );
}
