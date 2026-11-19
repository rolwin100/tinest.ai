"use client";

import { useMemo, useState } from "react";
import { tokenize, TOKEN_CLASS, type Language } from "@/lib/highlight";
import { cn } from "@/lib/cn";

export type Snippet = { label: string; language: Language; code: string };

export function CodeTabs({ snippets }: { snippets: Array<Snippet> }) {
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState(false);

  const snippet = snippets[active];
  const tokens = useMemo(
    () => tokenize(snippet.code, snippet.language),
    [snippet],
  );

  async function copy() {
    try {
      await navigator.clipboard.writeText(snippet.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard blocked — the code is selectable either way */
    }
  }

  return (
    <div className="overflow-hidden rounded-[var(--radius-feature)] border border-border bg-bg-sunken">
      <div className="flex items-center gap-1 border-b border-border px-2 py-1.5">
        {snippets.map((item, index) => (
          <button
            key={item.label}
            type="button"
            onClick={() => setActive(index)}
            className={cn(
              "rounded-full px-3 py-1.5 text-xs transition-colors duration-150 ease-[var(--ease-standard)]",
              index === active
                ? "bg-fg/8 text-fg"
                : "text-fg-subtle hover:text-fg-muted",
            )}
          >
            {item.label}
          </button>
        ))}
        <button
          type="button"
          onClick={copy}
          className="ml-auto rounded-full px-2.5 py-1.5 text-xs text-fg-subtle transition-colors duration-150 ease-[var(--ease-standard)] hover:text-fg"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <pre className="overflow-x-auto p-5 text-[13px] leading-[1.7] tracking-normal">
        <code className="font-mono">
          {tokens.map((token, index) => (
            <span key={index} className={TOKEN_CLASS[token.kind]}>
              {token.text}
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}
