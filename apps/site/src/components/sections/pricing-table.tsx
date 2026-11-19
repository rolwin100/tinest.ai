import Link from "next/link";
import { pricing } from "@/content/site";
import { CheckIcon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";

export function PricingTable({ withHeading = true }: { withHeading?: boolean }) {
  return (
    <section id="pricing" className="scroll-mt-20 border-t border-border py-24">
      <div className="shell">
        {withHeading ? (
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-overline text-accent">
              {pricing.eyebrow}
            </p>
            <h2 className="text-section mt-3 text-balance">{pricing.title}</h2>
            <p className="mt-4 text-base leading-relaxed text-pretty text-fg-muted">
              {pricing.sub}
            </p>
          </div>
        ) : null}

        <div className={cn("grid gap-5 lg:grid-cols-3", withHeading && "mt-14")}>
          {pricing.tiers.map((tier) => (
            <article
              key={tier.name}
              className={cn(
                "flex flex-col rounded-[var(--radius-feature)] border p-7",
                tier.featured
                  ? "border-accent bg-accent-soft"
                  : "border-border bg-bg-elevated",
              )}
            >
              <div className="flex items-center justify-between">
                <h3 className="font-medium tracking-tight">{tier.name}</h3>
                {tier.featured ? (
                  <span className="rounded-full bg-accent px-2.5 py-0.5 text-[11px] font-medium text-accent-fg">
                    Most popular
                  </span>
                ) : null}
              </div>

              <div className="mt-5 flex items-baseline gap-1">
                <span className="text-4xl font-light tracking-tight">{tier.price}</span>
                {tier.cadence ? (
                  <span className="text-sm text-fg-subtle">{tier.cadence}</span>
                ) : null}
              </div>

              <p className="mt-3 text-sm leading-relaxed text-fg-muted">{tier.blurb}</p>

              <ul className="mt-6 space-y-3 border-t border-border pt-6">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex gap-2.5 text-sm text-fg-muted">
                    <CheckIcon className="mt-0.5 size-3.5 shrink-0 text-accent" />
                    {feature}
                  </li>
                ))}
              </ul>

              <Link
                href="#"
                className={cn(
                  "mt-8 inline-flex h-11 items-center justify-center rounded-full px-5 text-[15px] transition-opacity duration-150 ease-[var(--ease-standard)] hover:opacity-88",
                  tier.featured
                    ? "bg-accent text-accent-fg"
                    : "bg-fg text-bg",
                )}
              >
                {tier.cta}
              </Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
