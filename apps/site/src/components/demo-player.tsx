"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { demoPrompts, voices } from "@/content/site";
import { Waveform } from "@/components/waveform";
import { Orb } from "@/components/orb";
import { PauseIcon, PlayIcon } from "@/components/ui/icons";
import { clipId, findClip } from "@/lib/samples";
import { cn } from "@/lib/cn";

/**
 * The hero demo. Deliberately plays pre-rendered clips rather than calling the
 * TTS server per visitor: a marketing page should not put a GPU in the path of
 * a first impression, and a static host can serve this from the edge.
 *
 * Clips come from `pnpm render:samples`, which speaks the real services/tts
 * wire protocol — so a visitor hears the genuine product, rendered early.
 *
 * Layout is orb left, controls right, vertically centred against each other —
 * the orb is the subject and the controls are the caption, which is the reading
 * order everything else on this page uses too.
 */
export function DemoPlayer() {
  const [voiceId, setVoiceId] = useState(voices.items[0].id);
  const [promptIndex, setPromptIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const activeVoice = voices.items.find((v) => v.id === voiceId) ?? voices.items[0];
  const prompts = demoPrompts[activeVoice.language] ?? demoPrompts["en-US"];
  const safeIndex = Math.min(promptIndex, prompts.length - 1);
  const prompt = prompts[safeIndex];

  const clip = useMemo(() => findClip(voiceId, safeIndex), [voiceId, safeIndex]);
  const seed = clipId(voiceId, safeIndex);

  // Changing voice or line resets playback rather than continuing the old clip.
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    setPlaying(false);
    setProgress(0);
  }, [voiceId, safeIndex]);

  function toggle() {
    const audio = audioRef.current;
    if (!audio || !clip) return;

    if (playing) {
      audio.pause();
      setPlaying(false);
      return;
    }

    void audio.play().then(
      () => setPlaying(true),
      () => setPlaying(false),
    );
  }

  function scrub(fraction: number) {
    const audio = audioRef.current;
    if (!audio || !clip || !Number.isFinite(audio.duration)) return;
    audio.currentTime = audio.duration * fraction;
    setProgress(fraction);
  }

  return (
    <div className="shadow-feature rounded-[var(--radius-feature)] border border-border bg-bg-elevated p-6 sm:p-9">
      <div className="flex flex-col gap-8 sm:flex-row sm:items-center sm:gap-10">
        {/*
          The voice's identity, and the only saturated colour on the page. The
          column is given a fixed width rather than letting the orb set it, so
          the right-hand block starts at the same x no matter what size the orb
          renders at — and so the orb has air around it instead of being shoved
          against the text.
        */}
        <div className="flex shrink-0 items-center justify-center sm:w-56 lg:w-64">
          <Orb
            seed={voiceId}
            motion={playing ? "live" : "idle"}
            blur={18}
            className="w-36 sm:w-44 lg:w-52"
          />
        </div>

        <div className="min-w-0 flex-1">
          {/*
            Labelled, not numbered. Numbered chips read as carousel pagination,
            which promises rotation the player does not do — and a label tells
            you what you are about to hear, which a number never can.
          */}
          <div className="inline-flex gap-0.5 rounded-full border border-border bg-bg-sunken p-1">
            {prompts.map((item, index) => (
              <button
                key={item.label}
                type="button"
                onClick={() => setPromptIndex(index)}
                className={cn(
                  "rounded-full px-2.5 py-1 text-[12px] transition-colors duration-150 ease-(--ease-standard)",
                  index === safeIndex
                    ? "bg-bg-elevated text-fg font-medium shadow-[0_1px_3px_oklch(0_0_0/10%)]"
                    : "text-fg-muted hover:text-fg",
                )}
                aria-pressed={index === safeIndex}
              >
                {item.label}
              </button>
            ))}
          </div>

          <p className="mt-5 text-xl leading-snug font-medium text-gray-700 tracking-tight sm:text-2xl">
            &ldquo;{prompt.text}&rdquo;
          </p>

          <div className="mt-6 flex items-center gap-4">
            <button
              type="button"
              onClick={toggle}
              disabled={!clip}
              aria-label={playing ? "Pause" : "Play"}
              className={cn(
                "grid size-12 shrink-0 place-items-center rounded-full transition-transform duration-150 ease-[var(--ease-standard)]",
                clip
                  ? "bg-fg text-bg hover:scale-105 active:scale-95"
                  : "cursor-not-allowed bg-fg/10 text-fg-subtle",
              )}
            >
              {playing ? (
                <PauseIcon className="size-5" />
              ) : (
                <PlayIcon className="size-5 translate-x-px" />
              )}
            </button>

            <Waveform
              seed={seed}
              progress={progress}
              animated={playing}
              onScrub={clip ? scrub : undefined}
              className="flex-1 overflow-x-hidden"
            />
          </div>
        </div>
      </div>

      <div className="mt-8 flex flex-wrap gap-1.5 border-t border-border pt-6">
        {voices.items.map((voice) => (
          <button
            key={voice.id}
            type="button"
            onClick={() => setVoiceId(voice.id)}
            className={cn(
              "flex items-center gap-2 rounded-full border py-1 pr-3.5 pl-1 text-[13px] transition-colors duration-150 ease-[var(--ease-standard)]",
              voice.id === voiceId
                ? "border-border-strong bg-fg/5 text-fg"
                : "border-border text-fg-muted hover:border-border-strong hover:text-fg",
            )}
            aria-pressed={voice.id === voiceId}
          >
            <Orb seed={voice.id} className="w-5" blur={2} />
            {voice.name}
          </button>
        ))}
      </div>

      <p className="mt-4 text-[13px] text-fg-subtle">
        {clip ? (
          <>
            {activeVoice.name} · {activeVoice.style} · {activeVoice.lang}
          </>
        ) : (
          <>
            No sample for {activeVoice.name} yet — run{" "}
            <code className="rounded bg-fg/8 px-1.5 py-0.5 font-mono text-xs">
              pnpm render:samples
            </code>{" "}
            with <code className="font-mono text-xs">just tts</code> running.
          </>
        )}
      </p>

      {clip ? (
        <audio
          ref={audioRef}
          src={clip.src}
          preload="none"
          onTimeUpdate={(event) => {
            const audio = event.currentTarget;
            if (Number.isFinite(audio.duration) && audio.duration > 0) {
              setProgress(audio.currentTime / audio.duration);
            }
          }}
          onEnded={() => {
            setPlaying(false);
            setProgress(0);
          }}
        />
      ) : null}
    </div>
  );
}
