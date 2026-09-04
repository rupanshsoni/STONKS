"use client";

import Shell from "@/components/shell/Shell";
import { useDeskStore } from "@/lib/store";
import { fmtUSD } from "@/lib/format";
import { Shield, ShieldAlert, CheckCircle, XCircle, AlertTriangle, Scale, Gauge, ListChecks } from "lucide-react";

const GATE_RULES: Record<string, string> = {
  SANITY: "Quotes fresh ≤ 120s, bid/ask spread sane, prices positive",
  REGIME: "Structure mathematically matched to VIX volatility band + GEX sign",
  VRP_EDGE: "Volatility Risk Premium (IV vs RV) spread ≥ calibrated edge threshold",
  EVENT_RISK: "Zero entry inside macro earnings/CPI/FOMC blackout window",
  DEFINED_RISK: "Atomic multi-leg structure required; max theoretical loss structurally capped",
  LIQUIDITY: "Open interest on each leg ≥ 250 contracts, spread ≤ 25% of mid",
  CREDIT_QUALITY: "Net credit received ≥ 15% of total wing width",
  POSITION_SIZE: "Single structure max premium risked ≤ 1.0% of portfolio NAV",
  PORTFOLIO_RISK: "Total active options risk across all books capped at ≤ 5.0% NAV",
  CONCENTRATION: "Strict maximum of ≤ 2 active structures per underlying ticker",
  DUPLICATE: "Deterministic client order ID collision prevention & dry-run validation",
  DAILY_HALT: "If daily portfolio P&L drops worse than −2.0% NAV → immediate halt & flatten",
};

const GATE_ORDER = Object.keys(GATE_RULES);

export default function RiskPage() {
  const state = useDeskStore((s) => s.state);
  const stats = state?.gate_stats ?? [];
  const config = (state?.config_snapshot ?? {}) as Record<string, number | string | string[]>;
  const params = state?.param_history ?? [];
  const dayPnl = state?.kpis.today_pnl ?? 0;
  const equity = state?.kpis.portfolio_value ?? 0;
  const haltPct = (Number(config.daily_halt_pct ?? 0.02) || 0.02);
  const haltLine = equity > 0 ? haltPct * equity : 0;
  const usage = Math.min(1, Math.abs(Math.min(dayPnl, 0)) / Math.abs(haltLine || 1));

  return (
    <Shell>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Sgt. Gate&apos;s Risk Wall
          <span className="pill text-[10px] border-amber-500/30 bg-amber-500/10 text-amber-400">
            Deterministic Kernel
          </span>
        </h1>
        <p className="text-xs md:text-sm text-text-secondary mt-1 max-w-2xl">
          Twelve code-enforced gates. Zero LLM hallucinations penetrate here. Every trade candidate is scored across all 12 gates without short-circuiting to record the exact margin of risk.
        </p>
      </div>

      {/* 12 Gates Radar Grid */}
      <section aria-label="Gate tiles" className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <Shield size={16} className="text-amber-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
            Deterministic Defense Matrix
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {GATE_ORDER.map((gate) => {
            const s = stats.find((x) => x.gate === gate);
            const rejects = s?.rejected ?? 0;
            const passes = s?.passed ?? 0;
            const total = passes + rejects;
            const lastLabel =
              s?.last_verdict === "pass" ? "PASS" : s?.last_verdict === "reject" ? "REJECT" : "READY";

            return (
              <div
                key={gate}
                className="card card-hover p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="num text-xs font-bold text-white tracking-wide">
                      {gate}
                    </span>
                    <span
                      className={`pill text-[10px] font-mono font-bold ${
                        lastLabel === "REJECT"
                          ? "pill-loss"
                          : lastLabel === "PASS"
                          ? "pill-profit"
                          : "border-white/10 bg-white/5 text-text-muted"
                      }`}
                    >
                      {lastLabel}
                    </span>
                  </div>

                  <p className="text-xs text-text-secondary leading-relaxed">
                    {GATE_RULES[gate]}
                  </p>
                </div>

                {total > 0 ? (
                  <div className="mt-3 pt-2 border-t border-white/5">
                    <div className="flex items-center justify-between text-[10px] font-mono text-text-muted mb-1">
                      <span className="text-emerald-400 font-bold">{passes} pass</span>
                      <span className="text-red-400 font-bold">{rejects} reject</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden flex">
                      <div
                        className="bg-emerald-400 h-full"
                        style={{ width: `${(passes / total) * 100}%` }}
                      />
                      <div
                        className="bg-red-400 h-full"
                        style={{ width: `${(rejects / total) * 100}%` }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-text-muted">
                    <span>Standing guard</span>
                    <span className="font-mono text-cyan-400">100% Active</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Halts & Exit Ladder Section */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 mb-8">
        {/* Daily Halt Meter */}
        <div className="card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Gauge size={16} className="text-red-400" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                Daily −{(haltPct * 100).toFixed(1)}% NAV Halt Line
              </h2>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">
              If daily losses exceed −{(haltPct * 100).toFixed(1)}% of portfolio equity, all positions are automatically flattened and all trading cycles are paused until market close.
            </p>

            <div className="mt-4 flex items-baseline justify-between">
              <div>
                <span className="text-[11px] text-text-muted block font-medium">Current Today P&amp;L</span>
                <span className="num text-2xl font-bold text-white">
                  {equity > 0 ? fmtUSD(dayPnl, true) : "—"}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[11px] text-text-muted block font-medium">Halt Threshold</span>
                <span className="num text-sm font-bold text-red-400">
                  {haltLine > 0 ? fmtUSD(-Math.abs(haltLine)) : "—"}
                </span>
              </div>
            </div>

            {/* Gauge bar */}
            <div className="mt-3 h-2 w-full rounded-full bg-white/5 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  usage > 0.6 ? "bg-red-500 shadow-[0_0_8px_#ef4444]" : "bg-cyan-400"
                }`}
                style={{ width: `${Math.max(5, usage * 100)}%` }}
              />
            </div>
          </div>

          <div className="mt-4 pt-2 border-t border-white/5 flex items-center justify-between text-xs text-text-muted">
            <span>Buffer Remaining: <strong className="text-emerald-400">{fmtUSD(Math.max(0, haltLine + dayPnl))}</strong></span>
            <span className="font-mono text-[11px] text-text-secondary">Circuit breaker active</span>
          </div>
        </div>

        {/* Exit Ladder Rules */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-2">
            <ListChecks size={16} className="text-cyan-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
              Automated Exit Ladder Protocol
            </h2>
          </div>
          <p className="text-xs text-text-secondary mb-3">
            Deterministic multi-tier profit targets and hard stop-loss executions:
          </p>

          <ul className="space-y-2 text-xs font-mono">
            <li className="flex items-center justify-between p-2 rounded-lg bg-[#060811] border border-white/5">
              <span className="text-emerald-400">Profit Target</span>
              <span className="text-white font-bold">{(((config.profit_target_pct as number) ?? 0.5) * 100).toFixed(0)}% of maximum credit collected</span>
            </li>
            <li className="flex items-center justify-between p-2 rounded-lg bg-[#060811] border border-white/5">
              <span className="text-red-400">Hard Stop Loss</span>
              <span className="text-white font-bold">{((config.hard_stop_multiple as number) ?? 2).toFixed(1)}× initial net credit received</span>
            </li>
            <li className="flex items-center justify-between p-2 rounded-lg bg-[#060811] border border-white/5">
              <span className="text-amber-400">Time Stop (DTE)</span>
              <span className="text-white font-bold">Close at {String(config.time_stop_dte ?? 21)} DTE</span>
            </li>
            <li className="flex items-center justify-between p-2 rounded-lg bg-[#060811] border border-white/5">
              <span className="text-purple-400">Event Blackout</span>
              <span className="text-white font-bold">No entries within {String(config.event_blackout_hours ?? 24)}h of scheduled events</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Honest Limitations Card */}
      <div className="card p-5 border-white/5 bg-[#080B15]/60">
        <h3 className="text-xs font-bold uppercase tracking-wider text-text-secondary mb-2">
          Mathematical &amp; Architecture Transparency
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-text-muted leading-relaxed">
          <p>
            • Free Alpaca options market data provides end-of-day Open Interest; intraday Gamma Exposure (GEX) is mathematically approximated.
          </p>
          <p>
            • 0DTE contracts are omitted due to non-continuous free feed pricing; 7–45 DTE defined-risk structures are prioritized.
          </p>
          <p>
            • Bid/Ask marking is strictly conservative (buy at ask, sell at bid) ensuring live reported P&amp;L never exaggerates performance.
          </p>
          <p>
            • Every order leg is submitted atomically via Alpaca multi-leg structure endpoints with strict price limits.
          </p>
        </div>
      </div>
    </Shell>
  );
}
