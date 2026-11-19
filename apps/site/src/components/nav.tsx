"use client";

import Link from "next/link";
import { useState } from "react";
import { nav, site } from "@/content/site";
import { LogoMark } from "@/components/ui/icons";
import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/cn";

export function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <header
      className="sticky top-0 z-[100] border-b border-border bg-bg"
    >
      <nav className="shell flex h-16 items-center gap-6">
        <Link href="/" className="flex items-center gap-2.5 font-medium tracking-tight">
          <LogoMark className="size-7 text-accent" />
          <span className="text-[15px]">{site.name}</span>
          <span className="text-[15px] text-fg-subtle">.ai</span>
        </Link>

        <ul className="ml-2 hidden items-center gap-1 md:flex">
          {nav.links.map((link) => (
            <li key={link.label}>
              <Link
                href={link.href}
                className="rounded-full px-3 py-2 text-sm text-fg-muted transition-colors duration-150 ease-[var(--ease-standard)] hover:bg-bg-elevated hover:text-fg"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          <Link
            href={nav.signIn.href}
            className="hidden rounded-full px-3 py-2 text-sm text-fg-muted transition-colors duration-150 ease-[var(--ease-standard)] hover:text-fg sm:block"
          >
            {nav.signIn.label}
          </Link>
          <Link
            href={nav.cta.href}
            className="hidden h-9 items-center rounded-full bg-fg px-4 text-sm text-bg transition-opacity duration-150 ease-[var(--ease-standard)] hover:opacity-88 sm:inline-flex"
          >
            {nav.cta.label}
          </Link>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
            aria-expanded={open}
            className="grid size-9 place-items-center rounded-full border border-border text-fg-muted md:hidden"
          >
            <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
              {open ? <path d="M6 6l12 12M18 6 6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
      </nav>

      {open ? (
        <div className="border-t border-border bg-bg md:hidden">
          <ul className="shell flex flex-col py-2">
            {nav.links.map((link) => (
              <li key={link.label}>
                <Link
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="block py-2.5 text-sm text-fg-muted"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </header>
  );
}
