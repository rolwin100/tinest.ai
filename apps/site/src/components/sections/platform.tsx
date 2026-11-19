import { platform } from "@/content/site";
import {
  AgentIcon,
  CheckIcon,
  FingerprintIcon,
  TranscriptIcon,
  WaveformIcon,
} from "@/components/ui/icons";

const icons = {
  waveform: WaveformIcon,
  fingerprint: FingerprintIcon,
  transcript: TranscriptIcon,
  agent: AgentIcon,
} as const;

export function Platform() {
  return (
    <section id="platform" className="scroll-mt-20 border-t border-border py-24">
      <div className="shell">
        <SectionHeading
          eyebrow={platform.eyebrow}
          title={platform.title}
          sub={platform.sub}
        />

        <div className="mt-14 grid gap-3 sm:grid-cols-2">
          {platform.products.map((product) => {
            const Icon = icons[product.icon as keyof typeof icons];
            return (
              <article
                key={product.id}
                className="rounded-[var(--radius-feature)] border border-border bg-bg-elevated p-8 transition-colors duration-200 ease-[var(--ease-standard)] hover:border-border-strong hover:bg-bg-sunken"
              >
<div className="flex size-12 items-center justify-center rounded-[var(--radius-control)] border border-border bg-bg text-accent">
                  <Icon className="size-5" />
                </div>
                <h3 className="mt-6 text-lg font-medium tracking-tight">{product.name}</h3>
                <p className="mt-2.5 text-sm leading-relaxed text-fg-muted">{product.blurb}</p>
                <ul className="mt-6 flex flex-wrap gap-x-4 gap-y-2">
                  {product.points.map((point) => (
                    <li key={point} className="flex items-center gap-1.5 text-xs text-fg-subtle">
                      <CheckIcon className="size-3 text-accent" />
                      {point}
                    </li>
                  ))}
                </ul>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  sub,
  align = "left",
}: {
  eyebrow?: string;
  title: string;
  sub?: string;
  align?: "left" | "center";
}) {
  return (
    <div className={align === "center" ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      {eyebrow ? (
        <p className="text-overline text-accent">{eyebrow}</p>
      ) : null}
      <h2 className="text-section mt-3 text-balance">{title}</h2>
      {sub ? (
        <p className="mt-4 text-base leading-relaxed text-pretty text-fg-muted">{sub}</p>
      ) : null}
    </div>
  );
}
