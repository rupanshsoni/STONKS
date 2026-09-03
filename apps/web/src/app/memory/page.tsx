"use client";

import Shell from "@/components/shell/Shell";
import { useDeskStore } from "@/lib/store";
import { timeAgo } from "@/lib/format";
import { Brain, ShieldAlert, ArrowRight, Lightbulb, History, Database } from "lucide-react";

const ROOT_CAUSE_LABEL: Record<string, string> = {
  thesis_wrong: "Thesis Invalidation",
  event_risk_underweighted: "Event Blackout Risk",
  timing_bad: "Entry Timing Misalignment",
  regime_shift: "Macro Regime Shift",
  luck: "Market Tail Variance",
};

export default function MemoryPage() {
  const state = useDeskStore((s) => s.state);
  const lessons = state?.lessons ?? [];
  const params = state?.param_history ?? [];

  return (
    <Shell>
      {/* Page Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Knowledge Vault (L3 Memory)
            <span className="pill text-[10px] border-orange-500/30 bg-orange-500/10 text-orange-400">
              Sage Memory Engine
            </span>
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1 max-w-3xl">
            The <strong>K</strong> in STONKS — Post-mortem learnings synthesized after trades.
            L3 lessons are injected into all future debate cycles, and parameter mutations are strictly <strong>restrict-only</strong>.
          </p>
        </div>
      </div>

      {/* L3 Lessons Section */}
      <section aria-label="Lessons learned" className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb size={16} className="text-orange-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
            Active Memory Rules &amp; Post-Mortems
          </h2>
        </div>

        {lessons.length ? (
          <div className="grid gap-4 md:grid-cols-2">
            {lessons.map((l) => (
              <div
                key={l.id}
                className="card p-5 border-orange-500/20 hover:border-orange-500/40 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="pill text-[10px] border-orange-500/30 bg-orange-500/10 text-orange-400 font-semibold">
                      {ROOT_CAUSE_LABEL[l.root_cause] ?? l.root_cause}
                    </span>
                    {l.applied_count > 0 && (
                      <span className="pill text-[10px] pill-profit">
                        Injected {l.applied_count}x
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-white font-medium leading-relaxed">
                    &ldquo;{l.text}&rdquo;
                  </p>

                  {l.failed_signal && (
                    <div className="mt-3 rounded-lg border border-white/5 bg-[#060811] p-2.5 text-xs text-text-secondary">
                      <span className="text-[10px] uppercase font-bold text-text-muted block">
                        Failed Signal
                      </span>
                      {l.failed_signal}
                    </div>
                  )}

                  {l.param_proposals.length > 0 && (
                    <div className="mt-3 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-text-muted block">
                        Parameter Tightenings
                      </span>
                      {l.param_proposals.map((p, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-2 text-xs font-mono text-emerald-400"
                        >
                          <span>{p.param}:</span>
                          <span className="text-text-muted">{p.current}</span>
                          <ArrowRight size={12} />
                          <span className="font-bold">{p.proposed}</span>
                          <span className="text-[10px] pill border-white/10 bg-white/5 text-text-secondary">
                            {p.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-text-muted">
                  <span>Trade ID: <code className="font-mono text-text-secondary">{l.trade_coid || "AUTO"}</code></span>
                  <span>{timeAgo(l.created_ts)}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center flex flex-col items-center justify-center gap-2">
            <div className="h-10 w-10 rounded-full border border-orange-500/20 bg-orange-500/5 flex items-center justify-center text-orange-400">
              <Brain size={18} />
            </div>
            <h3 className="font-semibold text-white text-sm">No Losses Recorded</h3>
            <p className="text-xs text-text-secondary max-w-md">
              The desk has maintained zero trigger-level losses in the current session. When a losing structure occurs, Sage immediately performs a post-mortem and registers lessons here.
            </p>
          </div>
        )}
      </section>

      {/* Restrict-Only Parameter History */}
      <section aria-label="Parameter history" className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <History size={16} className="text-emerald-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
            Restrict-Only Parameter Tightening Ledger
          </h2>
        </div>

        {params.length ? (
          <div className="card overflow-x-auto scroll-thin">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead>
                <tr className="border-b border-white/5 bg-white/[0.02] text-xs font-semibold uppercase tracking-wider text-text-muted">
                  <th className="px-4 py-3">Parameter</th>
                  <th className="px-4 py-3">Prior Bound</th>
                  <th className="px-4 py-3">Hardened Bound</th>
                  <th className="px-4 py-3">Motivated By</th>
                  <th className="px-4 py-3">Applied</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {params.map((p, i) => (
                  <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                    <td className="num px-4 py-3 font-semibold text-white">
                      {p.param}
                    </td>
                    <td className="num px-4 py-3 text-text-muted">
                      {p.before}
                    </td>
                    <td className="num px-4 py-3 font-bold text-emerald-400">
                      {p.after}
                    </td>
                    <td className="px-4 py-3 text-xs text-text-secondary">
                      {p.motivated_by || "Post-mortem analysis"}
                    </td>
                    <td className="px-4 py-3 text-xs text-text-muted font-mono">
                      {timeAgo(p.applied_at ?? "")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card p-6 text-center text-xs text-text-secondary">
            Initial parameter bounds active. Sage&apos;s restrictive updates land here upon loss detection.
          </div>
        )}
      </section>

      {/* L1 Snapshots & Ledger Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-2">
            <Database size={15} className="text-cyan-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
              L1 Rolling Market Snapshots
            </h3>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Point-in-time multi-underlying quotes, Black-Scholes Greeks, and implied-vs-realized volatility readings retained on a 24-hour rolling window.
          </p>
          <div className="mt-3 font-mono text-[11px] text-cyan-400">
            {state?.recent_events?.length ?? 0} active cycle events retained
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert size={15} className="text-purple-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-white">
              Restrict-Only Doctrine
            </h3>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Parameters can only become strictly more conservative. The kernel mechanically rejects loosening proposals regardless of model confidence.
          </p>
          <div className="mt-3 font-mono text-[11px] text-purple-400">
            Hard mathematical monotonicity enforced
          </div>
        </div>
      </div>
    </Shell>
  );
}
