import type { Metadata } from "next";
import { site } from "@/content/site";
import "@fontsource-variable/inter";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: `${site.domain} — ${site.tagline}`,
    template: `%s — ${site.domain}`,
  },
  description: site.description,
  metadataBase: new URL("https://gotiny.ai"),
  openGraph: {
    title: `${site.domain} — ${site.tagline}`,
    description: site.description,
    type: "website",
  },
};

/**
 * Applied before paint so a returning visitor's choice never flashes the wrong
 * palette. Default is LIGHT: both reference sites in design/design-dna.json are
 * warm off-white, and that is the register this design is tuned for. Dark is a
 * complete second palette, not a fallback.
 */
const themeScript = `
(function () {
  try {
    var stored = localStorage.getItem("gotiny-theme");
    if (stored === "dark") document.documentElement.classList.add("dark");
    else document.documentElement.classList.remove("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
