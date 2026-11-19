import { stats } from "@/content/site";

export function Stats() {
  return (
    <section className="border-t border-border py-24">
      <div className="shell">
        <div className="max-w-2xl">
          <h2 className="text-section text-balance">{stats.title}</h2>
          <p className="mt-4 text-base leading-relaxed text-pretty text-fg-muted">{stats.sub}</p>
        </div>

        <dl className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {stats.rows.map((row) => (
            <div key={row.label} className="rounded-[var(--radius-feature)] border border-border bg-bg-elevated p-8">
              <dt className="flex items-baseline gap-1">
                <span className="text-5xl font-light tracking-tight">{row.value}</span>
                <span className="text-xl font-medium text-fg-subtle">{row.unit}</span>
              </dt>
              <dd className="mt-4">
                <span className="block text-sm font-medium">{row.label}</span>
                <span className="mt-0.5 block text-xs text-fg-subtle">{row.note}</span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
