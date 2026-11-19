/**
 * Hand-drawn inline icons. No icon package: a marketing site should not pull a
 * dependency to draw nine shapes, and inline paths inherit currentColor and the
 * stroke width we actually want.
 */
type IconProps = { className?: string };

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function WaveformIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <path d="M3 12h1.5M7 8v8M11 4.5v15M15 7v10M19 10.5v3M21.5 12H21" />
    </svg>
  );
}

export function FingerprintIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <path d="M12 11v2a9 9 0 0 1-1.5 5" />
      <path d="M8.5 9.5a3.5 3.5 0 0 1 7 0V13a13 13 0 0 1-.8 4.5" />
      <path d="M5 12a7 7 0 0 1 11.4-5.4" />
      <path d="M18.8 9.5A7 7 0 0 1 19 12v1.5" />
      <path d="M5.2 16.5A7 7 0 0 0 6.6 19" />
    </svg>
  );
}

export function TranscriptIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <rect x="3" y="4" width="18" height="16" rx="2.5" />
      <path d="M7 9.5h6M7 13h10M7 16.5h4" />
    </svg>
  );
}

export function AgentIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <path d="M12 3v2" />
      <rect x="4" y="5" width="16" height="12" rx="3" />
      <path d="M9 10.5v1.5M15 10.5v1.5" />
      <path d="M8.5 21c1-1.2 2.2-1.8 3.5-1.8s2.5.6 3.5 1.8" />
    </svg>
  );
}

export function PlayIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M8 5.6c0-.9 1-1.5 1.8-1l8 6.4c.7.5.7 1.5 0 2l-8 6.4c-.8.5-1.8-.1-1.8-1V5.6Z" />
    </svg>
  );
}

export function PauseIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <rect x="7" y="5" width="3.5" height="14" rx="1.2" />
      <rect x="13.5" y="5" width="3.5" height="14" rx="1.2" />
    </svg>
  );
}

export function ArrowIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function CheckIcon({ className }: IconProps) {
  return (
    <svg {...base} strokeWidth={2} className={className} aria-hidden="true">
      <path d="M4.5 12.5 9 17l10.5-10.5" />
    </svg>
  );
}

export function SunIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4" />
    </svg>
  );
}

export function MoonIcon({ className }: IconProps) {
  return (
    <svg {...base} className={className} aria-hidden="true">
      <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
    </svg>
  );
}

export function LogoMark({ className }: IconProps) {
  return (
    <svg viewBox="0 0 28 28" className={className} aria-hidden="true">
      <rect width="28" height="28" rx="8" fill="currentColor" opacity="0.12" />
      <g stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M8 11.5v5" />
        <path d="M12.5 7.5v13" />
        <path d="M17 10v8" />
        <path d="M21 13v2" />
      </g>
    </svg>
  );
}
