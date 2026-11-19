import Link from "next/link";
import { closing } from "@/content/site";
import { ArrowIcon } from "@/components/ui/icons";

export function ClosingCta() {
  return (
    <section className="relative border-t border-border bg-bg-elevated">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="aurora-blob aurora-drift-1"
          style={{
            width: "65%",
            height: "90%",
            top: "-30%",
            left: "18%",
            background:
              "radial-gradient(ellipse, oklch(0.72 0.11 208 / 0.30) 0%, transparent 68%)",
          }}
        />
        <div
          className="aurora-blob aurora-drift-2"
          style={{
            width: "50%",
            height: "70%",
            top: "10%",
            right: "0%",
            background:
              "radial-gradient(ellipse, oklch(0.62 0.14 285 / 0.22) 0%, transparent 68%)",
          }}
        />
        <div
          className="aurora-blob aurora-drift-3"
          style={{
            width: "40%",
            height: "60%",
            bottom: "-10%",
            left: "0%",
            background:
              "radial-gradient(ellipse, oklch(0.70 0.12 55 / 0.15) 0%, transparent 68%)",
          }}
        />
        <div className="dot-grid absolute inset-0 opacity-25" />
      </div>

      <div className="shell relative z-10 py-36 text-center">
        <p className="text-overline text-accent">Get started</p>

        <h2 className="mx-auto mt-4 max-w-3xl text-balance text-[clamp(2rem,3.5vw,2.75rem)] font-semibold leading-[1.1] tracking-[-0.02em] text-fg">
          {closing.title}
        </h2>

        <p className="mx-auto mt-6 max-w-lg text-lg leading-relaxed text-pretty text-fg-muted">
          {closing.sub}
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href={closing.primary.href}
            className="group inline-flex h-12 w-full items-center justify-center gap-2 rounded-full bg-accent px-7 text-[15px] font-semibold text-accent-fg transition-opacity duration-150 ease-[var(--ease-standard)] hover:opacity-88 sm:w-auto"
          >
            {closing.primary.label}
            <ArrowIcon className="size-4 transition-transform duration-150 group-hover:translate-x-0.5" />
          </Link>
          <Link
            href={closing.secondary.href}
            className="inline-flex h-12 w-full items-center justify-center rounded-full border border-border px-7 text-[15px] font-medium text-fg-muted transition-colors duration-150 ease-[var(--ease-standard)] hover:border-border-strong hover:text-fg sm:w-auto"
          >
            {closing.secondary.label}
          </Link>
        </div>
      </div>
    </section>
  );
}
