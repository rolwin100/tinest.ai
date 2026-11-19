import Image from "next/image";
import { showcase } from "@/content/site";

const images: Record<string, string> = {
  "Support lines": "/support-lines.jpg",
  "Audio content": "/audio-content.jpg",
  "In-product voice": "/In-product-voice.jpg",
  "Dubbing and localisation": "/DubbingAndlocalisation.jpg",
};

export function UseCases() {
  return (
    <section className="border-t border-border py-24">
      <div className="shell">
        <div className="max-w-2xl">
          <p className="text-overline text-accent">
            {showcase.eyebrow}
          </p>
          <h2 className="text-section mt-3 text-balance">{showcase.title}</h2>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2">
          {showcase.items.map((item, index) => (
            <article
              key={item.name}
              className="overflow-hidden rounded-[var(--radius-feature)] border border-border bg-bg-elevated"
            >
              {images[item.name] && (
                <div className="relative aspect-[16/9] overflow-hidden">
                  <Image
                    src={images[item.name]}
                    alt={item.name}
                    fill
                    sizes="(max-width: 640px) 100vw, 50vw"
                    className="object-cover transition-transform duration-500 ease-[var(--ease-standard)] hover:scale-110"
                  />
                </div>
              )}
              <div className="p-6">
                <span className="font-mono text-xs text-fg-subtle">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="mt-2 font-medium tracking-tight">{item.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-fg-muted">{item.blurb}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
