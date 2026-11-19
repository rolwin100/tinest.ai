"use client";

import { useRef, useState } from "react";
import { voices } from "@/content/site";
import { Waveform } from "@/components/waveform";
import { Orb } from "@/components/orb";
import { PauseIcon, PlayIcon } from "@/components/ui/icons";
import { findClip } from "@/lib/samples";
import { cn } from "@/lib/cn";

/**
 * One <audio> element shared by the whole grid. Six elements would mean six
 * clips able to play at once, which is exactly the demo nobody wants.
 */
export function VoiceLibrary() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  function play(voiceId: string, src: string) {
    const audio = audioRef.current;
    if (!audio) return;

    if (activeId === voiceId) {
      audio.pause();
      setActiveId(null);
      return;
    }

    audio.src = src;
    setProgress(0);
    void audio.play().then(
      () => setActiveId(voiceId),
      () => setActiveId(null),
    );
  }

  return (
    <section id="voices" className="scroll-mt-20 border-t border-border bg-bg-sunken py-24">
      <div className="shell">
        <div className="max-w-2xl">
          <p className="text-overline text-accent">
            {voices.eyebrow}
          </p>
          <h2 className="text-section mt-3 text-balance">{voices.title}</h2>
          <p className="mt-4 text-base leading-relaxed text-pretty text-fg-muted">{voices.sub}</p>
        </div>

        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {voices.items.map((voice) => {
            const clip = findClip(voice.id, 0);
            const isActive = activeId === voice.id;

            return (
              <article
                key={voice.id}
                className={cn(
                  "rounded-[var(--radius-card)] border bg-bg-elevated p-5 transition-colors duration-150 ease-[var(--ease-standard)]",
                  isActive ? "border-accent" : "border-border hover:border-border-strong",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <Orb
                      seed={voice.id}
                      motion={isActive ? "live" : "still"}
                      className="w-10"
                      blur={4}
                    />
                    <div className="min-w-0">
                      <h3 className="font-medium tracking-tight">{voice.name}</h3>
                      <p className="mt-0.5 text-xs text-fg-subtle">{voice.style}</p>
                    </div>
                  </div>
                  <span className="rounded-full border border-border px-2 py-0.5 text-[11px] text-fg-subtle">
                    {voice.lang}
                  </span>
                </div>

                <div className="mt-5 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => clip && play(voice.id, clip.src)}
                    disabled={!clip}
                    aria-label={`${isActive ? "Pause" : "Play"} ${voice.name}`}
                    className={cn(
                      "grid size-9 shrink-0 place-items-center rounded-full transition-transform",
                      clip
                        ? "bg-fg text-bg hover:scale-105 active:scale-95"
                        : "cursor-not-allowed bg-fg/10 text-fg-subtle",
                    )}
                  >
                    {isActive ? (
                      <PauseIcon className="size-3.5" />
                    ) : (
                      <PlayIcon className="size-3.5 translate-x-px" />
                    )}
                  </button>
                  <Waveform
                    seed={voice.id}
                    bars={40}
                    progress={isActive ? progress : 0}
                    animated={isActive}
                    className="h-9 flex-1"
                  />
                </div>

                <p className="mt-4 font-mono text-[11px] text-fg-subtle">{voice.id}</p>
              </article>
            );
          })}
        </div>

        <audio
          ref={audioRef}
          preload="none"
          onTimeUpdate={(event) => {
            const audio = event.currentTarget;
            if (Number.isFinite(audio.duration) && audio.duration > 0) {
              setProgress(audio.currentTime / audio.duration);
            }
          }}
          onEnded={() => {
            setActiveId(null);
            setProgress(0);
          }}
        />
      </div>
    </section>
  );
}
