import Image from "next/image";
import Link from "next/link";
import { hero } from "@/content/site";
import { DemoPlayer } from "@/components/demo-player";
import { ArrowIcon } from "@/components/ui/icons";

export function Hero() {
  return (
    <section className="relative bg-bg">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <Image
          src="/hero-section.jpg"
          alt=""
          fill
          className="object-cover opacity-30"
          priority
        />
        <div
          className="aurora-blob aurora-drift-1"
          style={{
            width: "70%",
            height: "55%",
            top: "-15%",
            left: "15%",
            background:
              "radial-gradient(ellipse, oklch(0.72 0.11 208 / 0.22) 0%, transparent 70%)",
          }}
        />
        <div
          className="aurora-blob aurora-drift-2"
          style={{
            width: "55%",
            height: "45%",
            top: "5%",
            right: "-10%",
            background:
              "radial-gradient(ellipse, oklch(0.62 0.14 285 / 0.18) 0%, transparent 70%)",
          }}
        />
        <div
          className="aurora-blob aurora-drift-3"
          style={{
            width: "45%",
            height: "40%",
            top: "10%",
            left: "-5%",
            background:
              "radial-gradient(ellipse, oklch(0.70 0.12 55 / 0.12) 0%, transparent 70%)",
          }}
        />
        <div className="dot-grid absolute inset-0 opacity-40" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-linear-to-b from-transparent to-bg" />
      </div>

      <div className="shell relative z-10 pt-20 pb-24 sm:pt-28 sm:pb-32">
        <span className="animate-fade-up inline-flex items-center gap-2 rounded-full border border-border bg-bg-elevated px-3 py-1 text-[13px] text-fg-muted">
          <span className="size-1.5 rounded-full bg-accent" />
          {hero.eyebrow}
        </span>

        <div className="mt-8 grid gap-x-12 gap-y-8 lg:grid-cols-12 lg:items-center">
          <h1 className="animate-fade-up text-balance [animation-delay:60ms] lg:col-span-7 text-[clamp(2.75rem,5.5vw,4.25rem)] font-semibold leading-[1.06] ease-(--ease-standard)">
            {hero.headline[0]}
            <br />
            <span className="text-accent">{hero.headline[1]}</span>
          </h1>

          <p className="animate-fade-up text-pretty text-xl leading-relaxed text-fg-muted [animation-delay:120ms] lg:col-span-5">
            {hero.sub}
          </p>
        </div>

        <div className="animate-fade-up mt-10 flex flex-col gap-3 sm:flex-row [animation-delay:180ms]">
          <Link
            href={hero.primary.href}
            className="group inline-flex h-11 items-center justify-center gap-2 rounded-full bg-fg px-6 text-[15px] text-bg transition-opacity duration-150 ease-(--ease-standard) hover:opacity-88"
          >
            {hero.primary.label}
            <ArrowIcon className="size-4 transition-transform duration-150 group-hover:translate-x-0.5" />
          </Link>
          <Link
            href={hero.secondary.href}
            className="inline-flex h-11 items-center justify-center rounded-full border border-border px-6 text-[15px] text-fg-muted transition-colors duration-150 ease-(--ease-standard) hover:border-border-strong hover:text-fg"
          >
            {hero.secondary.label}
          </Link>
        </div>

        <div className="animate-fade-up mt-28 sm:mt-36 [animation-delay:240ms]">
          <DemoPlayer />
        </div>

        <dl className="animate-fade-up mt-14 grid grid-cols-2 overflow-hidden rounded-card border border-border bg-border/50 sm:grid-cols-4 [animation-delay:300ms]">
          {hero.proof.map((item) => (
            <div key={item.label} className="bg-bg-elevated/70 px-6 py-6">
              <dt className="text-3xl font-semibold tracking-tight text-gray-600">{item.value}</dt>
              <dd className="mt-1.5 text-sm font-medium text-fg-muted">{item.label}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
