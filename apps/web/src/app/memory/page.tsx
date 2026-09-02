"use client";

import Shell from "@/components/shell/Shell";
import { useDeskStore } from "@/lib/store";
import { timeAgo } from "@/lib/format";

const ROOT_CAUSE_LABEL: Record<string, string> = {
  thesis_wrong: "thesis wrong",
  event_risk_underweighted: "event risk underweighted",
  timing_bad: "timing bad",
  regime_shift: "regime shift",
  luck: "luck",
};

export default function MemoryPage() {
  const state = useDeskStore((s) => s.state);
  const lessons = state?.lessons ?? [];
  const params = state?.param_history ?? [];

  return (
    <Shell>
      <h1 className="mb-1 text-2xl font-bold">Memory</h1>
      <p className="mb-4 text-sm text-text-secondary">
        The K in STONKS — lessons the desk wrote itself after losses. L3 memory is
        injected into every future debate, and it can only make the desk more
        careful.
      </p>

      <section aria-label="Lessons learned">
        <h2 className="mb-2 text-base font-semibold">Lessons (L3)</h2>
        {lessons.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {lessons.map((l) => (
              <div key={l.id} className="card border-sage/30 p-4">
                <p className="text-sm">{l.text}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
                  <span className="pill border-sage/40 text-sage">
                    {ROOT_CAUSE_LABEL[l.root_cause] ?? l.root_cause}
                  </span>
                  {l.failed_signal && (
                    <span className="pill border-border-soft text-text-secondary">
                      failed signal: {l.failed_signal}
                    </span>
                  )}
                  {l.applied_count > 0 && (
                    <span className="pill border-profit/40 text-profit">
                      applied {l.applied_count}×
                    </span>
                  )}
                </div>
                {l.param_proposals.length > 0 && (
                  <ul className="mt-2 space-y-1 text-xs">
                    {l.param_proposals.map((p, i) => (
                      <li key={i} className={p.status === "applied" ? "text-profit" : "text-warning"}>
                        {p.param}: {p.current} → {p.proposed} ({p.status}
                        {p.reason ? ` — ${p.reason}` : ""})
                      </li>
                    ))}
                  </ul>
                )}
                {l.blocked_trades.length > 0 && (
                  <p className="mt-2 text-xs text-profit">
                    Blocked later: {l.blocked_trades.join(", ")}
                  </p>
                )}
                <p className="num mt-2 text-[10px] text-text-muted">
                  {timeAgo(l.created_ts)} · trade {l.trade_coid || "?"}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="card p-6 text-center text-sm text-text-secondary">
            No lessons yet — the desk hasn&apos;t been burned. Sage writes a lesson
            for every losing trade above the post-mortem trigger.
          </div>
        )}
      </section>

      <section className="mt-6" aria-label="Parameter history">
        <h2 className="mb-2 text-base font-semibold">The desk got more careful</h2>
        {params.length ? (
          <div className="card overflow-x-auto scroll-thin">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-soft text-left text-xs text-text-muted">
                  <th className="px-3 py-2 font-medium">Parameter</th>
                  <th className="px-3 py-2 font-medium">Before</th>
                  <th className="px-3 py-2 font-medium">After</th>
                  <th className="px-3 py-2 font-medium">Motivated by</th>
                  <th className="px-3 py-2 font-medium">When</th>
                </tr>
              </thead>
              <tbody>
                {params.map((p, i) => (
                  <tr key={i} className="border-b border-border-soft/50">
                    <td className="num px-3 py-2">{p.param}</td>
                    <td className="num px-3 py-2 text-text-secondary">{p.before}</td>
                    <td className="num px-3 py-2 text-profit">{p.after}</td>
                    <td className="num px-3 py-2 text-xs text-text-muted">{p.motivated_by || "—"}</td>
                    <td className="px-3 py-2 text-xs text-text-muted">{timeAgo(p.applied_at ?? "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card p-4 text-sm text-text-secondary">
            No parameter changes yet — Sage&apos;s restrict-only proposals land here.
          </div>
        )}
      </section>

      <section className="mt-6" aria-label="L1 snapshots">
        <h2 className="mb-2 text-base font-semibold">L1 snapshot browser</h2>
        <div className="card p-4 text-sm text-text-secondary">
          Point-in-time market snapshots (24h rolling) power the analysts each
          cycle. {state?.recent_events?.length ?? 0} recent events retained in
          the live feed.
        </div>
      </section>

      <section className="mt-6" aria-label="L2 ledger">
        <h2 className="mb-2 text-base font-semibold">L2 position ledger</h2>
        {state?.positions?.length ? (
          <ul className="card divide-y divide-border-soft text-sm">
            {state.positions.map((p) => (
              <li key={p.coid} className="px-4 py-2">
                <span className="font-mono font-semibold">{p.symbol}</span>{" "}
                <span className="text-text-secondary">{p.kind}</span>{" "}
                <span className="num text-xs text-text-muted">{p.coid}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="card p-4 text-sm text-text-secondary">No open positions.</div>
        )}
      </section>
    </Shell>
  );
}
