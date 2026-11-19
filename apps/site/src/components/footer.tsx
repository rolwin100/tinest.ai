import Link from "next/link";
import { footer, site } from "@/content/site";
import { LogoMark } from "@/components/ui/icons";

export function Footer() {
  return (
    <footer className="border-t border-border bg-bg-sunken">
      <div className="shell py-16">
        <div className="grid gap-12 md:grid-cols-[1.5fr_repeat(3,1fr)]">
          <div>
            <Link href="/" className="flex items-center gap-2.5 font-medium tracking-tight">
              <LogoMark className="size-7 text-accent" />
              <span className="text-[15px]">{site.name}</span>
              <span className="text-[15px] text-fg-subtle">.ai</span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-fg-muted">
              {footer.blurb}
            </p>
          </div>

          {footer.columns.map((column) => (
            <div key={column.title}>
              <h3 className="text-overline text-fg-subtle">
                {column.title}
              </h3>
              <ul className="mt-4 space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-fg-muted transition-colors duration-150 ease-[var(--ease-standard)] hover:text-fg"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col gap-4 border-t border-border pt-8 text-sm text-fg-subtle sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} {site.domain}</p>
          <p className="max-w-lg text-xs leading-relaxed sm:text-right">{footer.note}</p>
        </div>
      </div>
    </footer>
  );
}
