import { Nav } from "@/components/nav";
import { Footer } from "@/components/footer";
import { Hero } from "@/components/sections/hero";
import { TrustedBy } from "@/components/sections/trusted-by";
import { Platform } from "@/components/sections/platform";
import { VoiceLibrary } from "@/components/sections/voice-library";
import { Developers } from "@/components/sections/developers";
import { Stats } from "@/components/sections/stats";
import { UseCases } from "@/components/sections/use-cases";
import { PricingTable } from "@/components/sections/pricing-table";
import { ClosingCta } from "@/components/sections/closing-cta";

export default function HomePage() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <TrustedBy />
        <Platform />
        <VoiceLibrary />
        <Developers />
        <Stats />
        <UseCases />
        <PricingTable />
        <ClosingCta />
      </main>
      <Footer />
    </>
  );
}
