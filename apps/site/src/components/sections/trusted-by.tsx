import { trustedBy } from "@/content/site";

export function TrustedBy() {
  return (
    <section className="border-b border-border bg-bg py-10">
      <div className="shell">
        <p className="mb-8 text-center text-[11px] font-medium tracking-[0.12em] uppercase text-fg-subtle">
          {trustedBy.eyebrow}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 md:gap-x-16">
          {trustedBy.logos.map((logo) => (
            // eslint-disable-next-line @next/next/no-img-element -- static
            // brand SVG with per-mark CSS filters; next/image adds nothing here.
            <img
              key={logo.file}
              src={`/client-logo/${logo.file}.svg`}
              alt={logo.name}
              className="h-5 w-auto shrink-0 opacity-45 grayscale transition-[opacity,filter] duration-150 hover:opacity-100 hover:grayscale-0 sm:h-7"
            />
          ))}
        </div>
      </div>
    </section>
  );
}
