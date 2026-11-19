import type { Metadata } from "next";
import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { PricingTable } from "@/components/sections/pricing-table";
import { ClosingCta } from "@/components/sections/closing-cta";
import { pricing } from "@/content/site";

export const metadata: Metadata = {
  title: "Pricing",
  description: pricing.sub,
};

export default function PricingPage() {
  return (
    <>
      <Nav />
      <main>
        <section className="relative overflow-hidden border-b border-border">
          <div className="accent-glow pointer-events-none absolute inset-x-0 top-0 h-80" />
          <div className="shell relative py-20 text-center">
            <p className="text-xs font-medium tracking-wider text-accent uppercase">
              {pricing.eyebrow}
            </p>
            <h1 className="text-display mx-auto mt-4 max-w-3xl text-balance">
              {pricing.title}
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-pretty text-fg-muted">
              {pricing.sub}
            </p>
          </div>
        </section>
        <PricingTable withHeading={false} />
        <ClosingCta />
      </main>
      <Footer />
    </>
  );
}
