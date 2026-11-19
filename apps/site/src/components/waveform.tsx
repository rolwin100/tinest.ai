"use client";

import { useMemo } from "react";
import { barHeights } from "@/lib/waveform";
import { cn } from "@/lib/cn";

type WaveformProps = {
  seed: string;
  /** 0 to 1. Bars before this point are drawn in the accent colour. */
  progress?: number;
  bars?: number;
  className?: string;
  /** Gentle idle motion when nothing is playing. */
  animated?: boolean;
  onScrub?: (fraction: number) => void;
};

export function Waveform({
  seed,
  progress = 0,
  bars = 72,
  className,
  animated = false,
  onScrub,
}: WaveformProps) {
  const heights = useMemo(() => barHeights(seed, bars), [seed, bars]);

  function handleClick(event: React.MouseEvent<HTMLDivElement>) {
    if (!onScrub) return;
    const rect = event.currentTarget.getBoundingClientRect();
    onScrub(Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)));
  }

  return (
    <div
      onClick={handleClick}
      className={cn(
        "flex h-14 items-center gap-[3px]",
        onScrub && "cursor-pointer",
        className,
      )}
      aria-hidden="true"
    >
      {heights.map((height, index) => {
        const played = index / heights.length <= progress;
        return (
          <span
            key={index}
            className={cn(
              "flex-1 rounded-full transition-colors duration-150",
              played ? "bg-accent" : "bg-fg/20",
            )}
            style={{
              height: `${Math.round(height * 100)}%`,
              minWidth: 2,
              ...(animated
                ? {
                    animation: `gotiny-bar ${1.1 + (index % 7) * 0.13}s ease-in-out ${index * 0.014}s infinite`,
                  }
                : null),
            }}
          />
        );
      })}
    </div>
  );
}
