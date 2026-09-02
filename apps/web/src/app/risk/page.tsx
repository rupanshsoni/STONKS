"use client";

import Shell from "@/components/shell/Shell";
import { useDeskStore } from "@/lib/store";
import { fmtUSD } from "@/lib/format";

const GATE_RULES: Record<string, string> = {
  SANITY: "quotes fresh ≤ 120s, prices positive",
  REGIME: "structure allowed by VIX band + GEX sign",
  VRP_EDGE: "implied-vs-realized edge ≥ threshold",
  EVENT_RISK: "no entry inside event blackout window",
  DEFINED_RISK: "atomic multi-leg, max loss structurally capped",
  LIQUIDITY: "leg OI ≥ 250, spread ≤ 25% of mid",
  CREDIT_QUALITY: "credit ≥ 15% of wing width",
  POSITION_SIZE: "premium risked ≤ 1.0% NAV",
  PORTFOLIO_RISK: "total open risk ≤ 5% NAV",
  CONCENTRATION: "≤ 2 structures per underlying",
  DUPLICATE: "deterministic coid + dry-run preview",
  DAILY_HALT: "day P&L worse than −2% NAV → flatten",
};

const GATE_ORDER = Object.keys(GATE_RULES);

export default function RiskPage() {
  const state = useDeskStore((s) => s.state);
  const stats = state?.gate_stats ?? [];
  const config = (state?.config_snapshot ?? {}) as Record<string, number | string | string[]>;
  const params = state?.param_history ?? [];
  const dayPnl = state?.kpis.today_pnl ?? 0;
  const equity = state?.kpis.portfolio_value ?? 100000;
  const haltLine = (Number(config.daily_halt_pct ?? 0.02) || 0.02) * equity;
  const usage = Math.min(1, Math.abs(Math.min(dayPnl, 0)) / Math.abs(haltLine || 1));

  return (
    <Shell>
      <h1 className="mb-1 text-2xl font-bold">Sgt. Gate&apos;s wall</h1>
      <p className="mb-4 max-w-2xl text-sm text-text-secondary">
        Twelve deterministic gates. No LLM judgment enters here — every verdict
        is code, config, and reason codes. All twelve are scored on every
        proposal so the journal records how badly a rejected trade failed.
      </p>

      <section aria-label="Gate tiles" className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
        {GATE_ORDER.map((gate) => {
          const s = stats.find((x) => x.gate === gate);
          const rejects = s?.rejected ?? 0;
          const passes = s?.passed ?? 0;
          const total = passes + rejects;
          const lastLabel =
            s?.last_verdict === "pass" ? "PASS" : s?.last_verdict === "reject" ? "REJECT" : "—";
          return (
            <div
              key={gate}
              className={`card p-4 ${rejects > 0 ? "border-warning/40" : ""}`}
            >
              <div className="flex items-center justify-between">
                <h2 className="num text-sm font-bold">{gate}</h2>
                <span
                  className={`pill ${
                    lastLabel === "REJECT"
                      ? "border-loss/40 text-loss"
                      : lastLabel === "PASS"
                        ? "border-profit/40 text-profit"
                        : "border-border-soft text-text-muted"
                  }`}
                >
                  {lastLabel}
                </span>
              </div>
              <p className="mt-1 text-xs text-text-secondary">{GATE_RULES[gate]}</p>
              {total > 0 && (
                <>
                  <div className="mt-2 flex items-center gap-2 text-[10px] text-text-muted">
                    <span className="num text-profit">{passes} pass</span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-border-soft">
                      <div
                        className="h-full bg-loss"
                        style={{ width: `${(rejects / total) * 100}%` }}
                      />
                    </div>
                    <span className="num text-loss">{rejects} reject</span>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </section>

      <section className="mt-6 grid gap-4 xl:grid-cols-2" aria-label="Halts and exits">
        <div className="card p-4">
          <h2 className="text-base font-semibold">Daily halt status</h2>
          <p className="num mt-1 text-2xl">{fmtUSD(dayPnl, true)}</p>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-border-soft">
            <div
              className={`h-full ${usage > 0.5 ? "bg-loss" : "bg-warning"}`}
              style={{ width: `${usage * 100}%` }}
            />
          </div>
          <p className="num mt-1 text-xs text-text-muted">
            halt line {fmtUSD(-Math.abs(haltLine))} (−
            {String(config.daily_halt_pct ?? 0.02)} NAV)
          </p>
        </div>

        <div className="card p-4">
          <h2 className="text-base font-semibold">Exit ladder</h2>
          <ul className="num mt-2 space-y-1 text-xs text-text-secondary">
            <li>profit target: 50% of max credit</li>
            <li>hard stop: 2× credit received</li>
            <li>time stop: close at {String(config.time_stop_dte ?? 21)} DTE</li>
            <li>wheel rolls at {String(config.wheel_roll_dte ?? 21)} DTE</li>
            <li>event rule: close before symbol earnings</li>
            <li>regime flip: close when entry regime inverts</li>
          </ul>
        </div>
      </section>

      <section className="mt-6" aria-label="Restrict-only history">
        <h2 className="mb-2 text-base font-semibold">
          Restrict-only — the desk can only get more careful
        </h2>
        {params.length ? (
          <ul className="card divide-y divide-border-soft text-sm">
            {params.map((p, i) => (
              <li key={i} className="num px-4 py-2">
                {p.param}: {p.before} → <span className="text-profit">{p.after}</span>{" "}
                <span className="text-xs text-text-muted">({p.motivated_by})</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="card p-4 text-sm text-text-secondary">
            Sage&apos;s tightenings land here, validated against hardcoded bounds
            — loosening is rejected by construction.
          </div>
        )}
      </section>

      <section className="mt-6" aria-label="Honest limitations">
        <div className="card p-4 text-xs leading-relaxed text-text-muted">
          <p className="mb-1 font-semibold text-text-secondary">Honest limitations</p>
          <p>Free-feed OI is end-of-day → intraday GEX is approximate (stated, not hidden).</p>
          <p>0DTE contracts are invisible in the free feed → no 0DTE engine.</p>
          <p>A ~1-week window is statistical noise → process metrics reported alongside P&amp;L.</p>
          <p>Bid/ask marking is conservative (buy ask / sell bid) → reported P&amp;L understates mid-mark.</p>
        </div>
      </section>
    </Shell>
  );
}
