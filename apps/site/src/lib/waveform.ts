import { hashSeed, mulberry32 } from "@/lib/seed";

/**
 * Speech-shaped bar heights, not noise-shaped: a slow envelope for phrases, a
 * faster one for syllables, and short near-silent gaps where breaths would be.
 * Derived from the clip id so it is stable across renders.
 */
export function barHeights(seed: string, count: number): Array<number> {
  const rand = mulberry32(hashSeed(seed));
  const bars: Array<number> = [];

  for (let i = 0; i < count; i++) {
    const t = i / count;
    const phrase = 0.55 + 0.45 * Math.sin(t * Math.PI * 2.2 + rand() * 0.4);
    const syllable = 0.6 + 0.4 * Math.sin(t * Math.PI * count * 0.22);
    const jitter = 0.7 + rand() * 0.6;

    let value = phrase * syllable * jitter;
    if (rand() > 0.94) value *= 0.18;

    const edge = Math.min(1, Math.min(t, 1 - t) * 14);
    value *= edge;

    bars.push(Math.max(0.08, Math.min(1, value)));
  }

  return bars;
}
