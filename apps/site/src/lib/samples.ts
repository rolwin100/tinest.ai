import manifest from "../../public/samples/manifest.json";

export type Clip = {
  id: string;
  voiceId: string;
  promptIndex: number;
  src: string;
  durationMs: number;
};

export type SampleManifest = {
  generatedAt: string | null;
  clips: Array<Clip>;
};

export const samples = manifest as SampleManifest;

export function clipId(voiceId: string, promptIndex: number) {
  return `${voiceId}:${promptIndex}`;
}

export function findClip(voiceId: string, promptIndex: number): Clip | null {
  const id = clipId(voiceId, promptIndex);
  return samples.clips.find((clip) => clip.id === id) ?? null;
}
