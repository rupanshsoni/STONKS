"use client";

import React, { useState } from "react";
import {
  Area,
  AreaChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowDownRight,
  ArrowUpRight,
  Activity,
  Wallet,
  TrendingUp,
  Gauge,
  Layers,
  Clock,
  ChevronDown,
  RefreshCw,
  Sparkles,
  BarChart3,
  CheckCircle2,
} from "lucide-react";
import Shell from "@/components/shell/Shell";
import { MascotChip } from "@/components/mascots/MascotAvatar";
import GateGrid from "@/components/GateGrid";
import { useDeskStore } from "@/lib/store";
import { fmtUSD, structureTag, timeAgo } from "@/lib/format";
import type { JournalEvent } from "@/lib/types";

// Ticking countdown to a future ISO timestamp; returns null when no target.
function useCountdown(iso: string | null | undefined): string | null {
  const [now, setNow] = useState(() => Date.now());
  React.useEffect(() => {
    if (!iso) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [iso]);
  if (!iso) return null;
  const diff = new Date(iso).getTime() - now;
  if (!(diff > 0)) return null;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// Glowing SVG Mini-Sparkline with Obsidian Blue theme styling
function MiniSparkline({
  color = "#00FF87",
  variant = "up",
}: {
  color?: string;
  variant?: "up" | "down" | "wave" | "steady";
}) {
  const paths = {
    up: "M0 24 Q18 20 35 14 T70 18 T105 8 T140 3",
    down: "M0 6 Q20 10 40 18 T80 12 T110 22 T140 26",
    wave: "M0 16 Q20 6 45 16 T85 10 T115 22 T140 12",
    steady: "M0 15 Q25 18 50 14 T90 16 T120 13 T140 15",
  };

  const peakDot = {
    up: { cx: 140, cy: 3 },
    down: { cx: 140, cy: 26 },
    wave: { cx: 85, cy: 10 },
    steady: { cx: 120, cy: 13 },
  }[variant];

  return (
    <div className="h-7 w-28 relative overflow-visible">
      <svg
        viewBox="0 0 140 30"
        fill="none"
        className="w-full h-full overflow-visible"
      >
        <defs>
          <filter id={`v2-glow-${variant}`} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor={color} floodOpacity="0.5" />
          </filter>
        </defs>
        <path
          d={paths[variant]}
          stroke={color}
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter={`url(#v2-glow-${variant})`}
        />
        <circle
          cx={peakDot.cx}
          cy={peakDot.cy}
          r="3"
          fill={color}
          stroke="#06080d"
          strokeWidth="1.2"
          filter={`url(#v2-glow-${variant})`}
        />
      </svg>
    </div>
  );
}

// 4 Performance Metric Cards
function MetricCard({
  label,
  value,
  sub,
  icon: Icon,
  pillText,
  pillPositive,
  sparklineColor = "#00FF87",
  sparklineVariant = "up",
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  pillText?: string;
  pillPositive?: boolean | null;
  sparklineColor?: string;
  sparklineVariant?: "up" | "down" | "wave" | "steady";
}) {
  return (
    <div className="card card-hover p-4 md:p-5 flex flex-col justify-between overflow-hidden group">
      {/* Background micro grid */}
      <div className="absolute inset-0 bg-grid-mesh opacity-40 pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between z-10 relative">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] transition-colors group-hover:border-white/20"
            style={{ color: sparklineColor, boxShadow: `0 0 12px ${sparklineColor}20` }}
          >
            <Icon size={15} aria-hidden />
          </div>
          <span className="text-xs font-medium text-text-secondary">{label}</span>
        </div>

        {pillText && (
          <span
            className={`pill text-[10.5px] ${
              pillPositive === true
                ? "pill-profit"
                : pillPositive === false
                ? "pill-loss"
                : "border-white/10 bg-white/5 text-text-secondary"
            }`}
          >
            {pillPositive === true && <ArrowUpRight size={11} />}
            {pillPositive === false && <ArrowDownRight size={11} />}
            {pillText}
          </span>
        )}
      </div>

      {/* Figures & Sparkline */}
      <div className="mt-3.5 flex items-end justify-between z-10 relative">
        <div>
          <div className="num text-2xl font-bold tracking-tight text-white">
            {value}
          </div>
          {sub && (
            <div className="num text-[11px] text-text-muted mt-0.5 font-medium">
              {sub}
            </div>
          )}
        </div>
        <MiniSparkline color={sparklineColor} variant={sparklineVariant} />
      </div>
    </div>
  );
}

// Live Activity Feed Card with crisp font formatting
function FeedCard({ e }: { e: JournalEvent }) {
  const isGate = e.type === "gate_verdict";
  const isDecision = e.type === "decision_card";
  const approved = e.data.approved;

  return (
    <div
      className="fade-enter group rounded-xl border border-white/5 bg-[#0b0e1a]/90 p-3 hover:border-white/10 hover:bg-[#0f1424] transition-all duration-150"
      aria-live="polite"
    >
      <div className="flex items-start gap-2.5">
        <MascotChip agent={e.agent} size={26} />
        <div className="min-w-0 flex-1">
          {/* Header row: Agent name, event type pill, symbol, timestamp */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <span className="font-semibold text-white text-[12px] tracking-wide">
              {e.agent === "desk" ? "The Desk" : e.agent.toUpperCase()}
            </span>
            <span
              className={`pill text-[9.5px] uppercase font-mono ${
                e.level === "error"
                  ? "pill-loss"
                  : e.level === "warn"
                  ? "pill-warning"
                  : "border-white/10 bg-white/5 text-text-secondary"
              }`}
            >
              {e.type.replace(/_/g, " ")}
            </span>
            {e.symbol && (
              <span className="pill font-mono text-[9.5px] font-bold border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
                {e.symbol}
              </span>
            )}
            <span className="ml-auto num text-[10px] text-text-muted">
              {timeAgo(e.ts)}
            </span>
          </div>

          {/* Narrative Summary - Fixed compact font size */}
          <p className="mt-1 text-xs text-text-primary leading-relaxed">
            {e.summary}
          </p>

          {/* Gate result grid if present */}
          {isGate && e.data.results && (
            <div className="mt-2 pt-2 border-t border-white/5">
              <GateGrid results={e.data.results} />
              {approved === false && (
                <p className="mt-1 text-[11px] font-semibold text-amber-400">
                  REJECTED — {e.data.results.find((r) => !r.passed)?.reason_code ?? "RISK_BOUND"}
                </p>
              )}
            </div>
          )}

          {/* Decision card debate conviction scores (render only when journaled) */}
          {isDecision && e.data.verdict && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
              {(e.data.rounds ?? [])
                .filter((r) => r && typeof r.conviction === "number")
                .map((r, i) => (
                  <span
                    key={i}
                    className={`pill text-[9.5px] ${
                      r.agent === "ursa"
                        ? "border-red-500/30 bg-red-500/10 text-red-400"
                        : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                    }`}
                  >
                    {(r.agent ?? (i === 0 ? "TORO" : "URSA")).toUpperCase()} {r.conviction.toFixed(1)}
                  </span>
                ))}
              <span className="pill text-[9.5px] border-purple-500/30 bg-purple-500/10 text-purple-300">
                VERDI: {e.data.verdict.direction} ({e.data.verdict.conviction.toFixed(2)})
              </span>
            </div>
          )}

          {/* Model info chip */}
          {e.model && (
            <span className="num mt-1 inline-block text-[10px] text-text-muted font-mono">
              Engine: {e.model}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// Open Positions Table
function PositionsTable() {
  const state = useDeskStore((s) => s.state);
  const positions = state?.positions ?? [];

  if (!positions.length) {
    return (
      <div className="card p-7 text-center flex flex-col items-center justify-center gap-2.5">
        <div className="h-9 w-9 rounded-full border border-cyan-500/20 bg-cyan-500/5 flex items-center justify-center text-cyan-400 animate-pulse">
          <RefreshCw size={16} />
        </div>
        <div>
          <h3 className="font-semibold text-white text-xs">No Open Structures</h3>
          <p className="text-[11px] text-text-muted mt-0.5">
            {state?.market?.open
              ? "The desk is scanning the options chain — next cycle every 30m."
              : "Market closed — the desk sleeps and reopens with the next session."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-x-auto scroll-thin">
      <table className="w-full text-left text-xs whitespace-nowrap">
        <thead>
          <tr className="border-b border-white/5 bg-white/[0.02] font-semibold uppercase tracking-wider text-text-muted text-[10.5px]">
            <th className="px-4 py-3">Symbol</th>
            <th className="px-4 py-3">Structure</th>
            <th className="px-4 py-3">Contracts</th>
            <th className="px-4 py-3">Entry Credit</th>
            <th className="px-4 py-3">Current Mark</th>
            <th className="px-4 py-3">Unrealized P&amp;L</th>
            <th className="px-4 py-3">DTE</th>
            <th className="px-4 py-3">Exit Protocol</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {positions.map((p) => {
            const marked = p.current_mark != null && p.unrealized_pnl != null;
            const isProfit = marked && (p.unrealized_pnl as number) >= 0;
            return (
              <tr
                key={p.coid}
                className="hover:bg-white/[0.02] transition-colors"
              >
                <td className="px-4 py-3 font-mono font-bold text-white">
                  <div className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                    {p.symbol}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="pill text-[10.5px] border-white/10 bg-white/5 text-text-secondary">
                    {structureTag(p.kind)}
                  </span>
                </td>
                <td className="num px-4 py-3 font-medium text-text-primary">
                  {p.qty}x
                </td>
                <td className="num px-4 py-3 text-text-secondary">
                  {fmtUSD(p.entry_credit)}
                </td>
                <td className="num px-4 py-3 text-text-secondary">
                  {marked ? fmtUSD(p.current_mark as number) : "—"}
                </td>
                <td className="px-4 py-3">
                  {marked ? (
                    <span
                      className={`pill font-mono text-[11px] ${
                        isProfit ? "pill-profit" : "pill-loss"
                      }`}
                    >
                      {isProfit ? "▲" : "▼"} {fmtUSD(p.unrealized_pnl as number, true)}
                    </span>
                  ) : (
                    <span className="pill font-mono text-[11px] border-white/10 bg-white/5 text-text-muted">
                      marking…
                    </span>
                  )}
                </td>
                <td className="num px-4 py-3 font-mono text-[11px] text-text-secondary">
                  <span className="inline-flex items-center gap-1">
                    <Clock size={11} className="text-text-muted" />
                    {p.dte} DTE
                  </span>
                </td>
                <td className="px-4 py-3 text-[11px] text-text-secondary">
                  <span className="pill text-[9.5px] border-white/10 bg-white/5">
                    {p.exit_status}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function OverviewPage() {
  const state = useDeskStore((s) => s.state);
  const events = useDeskStore((s) => s.events);
  const [timeRange, setTimeRange] = useState<"1s" | "15m" | "1h" | "4h" | "1d" | "1w">("1d");
  const [lossTab, setLossTab] = useState<"max" | "current">("current");

  const kpis = state?.kpis;
  const rawCurve = state?.equity_curve ?? [];
  const market = state?.market;
  const baseline = state?.account?.baseline ?? 100000;

  // Live equity curve only — no fabricated backfill. When the desk has not
  // completed enough cycles to draw a curve, we show the single live point
  // state honestly instead of inventing a history.
  const curve = rawCurve.map((p) => ({
    ts: new Date(p.ts).getTime(),
    equity: p.equity,
  }));

  const currentEquity = kpis?.portfolio_value ?? 0;
  const dayPnl = kpis?.today_pnl ?? 0;
  const haltPct = Number(state?.config_snapshot?.daily_halt_pct ?? 0.02);
  const dailyHaltLine = currentEquity > 0 ? currentEquity * haltPct : 0;
  const dayLossUsedPct =
    dailyHaltLine > 0
      ? Math.min(100, Math.max(0, (Math.abs(Math.min(dayPnl, 0)) / dailyHaltLine) * 100))
      : 0;
  const dayStartEquity = currentEquity - dayPnl;
  const riskUsedPct = kpis?.risk_used_pct ?? 0;
  const riskCapPct = Number(state?.config_snapshot?.max_portfolio_risk_pct ?? 0.05);
  const openRiskUsd = currentEquity * riskUsedPct;
  const gatePassed = (state?.gate_stats ?? []).reduce((a, g) => a + g.passed, 0);
  const gateRejected = (state?.gate_stats ?? []).reduce((a, g) => a + g.rejected, 0);
  const gateTotal = gatePassed + gateRejected;
  const nextClock = market?.open ? market?.next_close : market?.next_open;
  const clockValue = useCountdown(nextClock) ?? (nextClock ? new Date(nextClock).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—");

  return (
    <Shell>
      {/* =================================================================== */}
      {/* 1. TOP SPLIT PANE: Hero Chart (66%) + Account Loss Analysis (34%)  */}
      {/* =================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-4">
        {/* Left Hero: Portfolio Balance & Equity Curve */}
        <section
          className="card p-5 lg:col-span-8 flex flex-col justify-between"
          aria-label="Equity Curve Chart"
        >
          {/* Header Row */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-cyan-500/20 bg-cyan-500/10 text-cyan-400">
                <Wallet size={16} />
              </div>
              <div>
                <span className="text-[11px] font-medium uppercase tracking-wider text-text-muted block">
                  Balance
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="num text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                    {currentEquity > 0 ? fmtUSD(currentEquity) : "—"}
                  </span>
                  <span className="text-xs font-mono font-semibold text-text-secondary">
                    USD
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Controls */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 border border-white/5 bg-white/[0.03] p-1 rounded-xl">
                {(["1s", "15m", "1h", "4h", "1d", "1w"] as const).map((r) => (
                  <button
                    key={r}
                    onClick={() => setTimeRange(r)}
                    className={`rounded-lg px-2 py-0.5 text-[10.5px] font-mono font-medium transition-all ${
                      timeRange === r
                        ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-bold shadow-[0_0_10px_rgba(0,229,255,0.15)]"
                        : "text-text-muted hover:text-white border border-transparent"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>

              <div className="hidden sm:flex items-center gap-1.5 rounded-xl border border-white/5 bg-white/[0.03] px-2.5 py-1 text-xs text-text-secondary cursor-pointer hover:border-white/10">
                <span className="text-[11px]">7 Days</span>
                <ChevronDown size={12} className="text-text-muted" />
              </div>
            </div>
          </div>

          {/* Glowing Continuous Line Chart — live points only */}
          <div className="h-[280px] w-full min-h-[280px]">
            {curve.length > 1 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={curve} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00E5FF" stopOpacity={0.35} />
                    <stop offset="90%" stopColor="#00E5FF" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="ts"
                  tickFormatter={(t) =>
                    new Date(t).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  }
                  stroke="#1c2444"
                  tick={{ fontSize: 10.5, fill: "#5a6480" }}
                  tickLine={false}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  stroke="#1c2444"
                  tick={{ fontSize: 10.5, fill: "#5a6480" }}
                  tickLine={false}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                  allowDataOverflow={false}
                  padding={{ top: 20, bottom: 20 }}
                />
                {currentEquity > 0 && (
                  <ReferenceLine
                    y={baseline}
                    stroke="#2a3560"
                    strokeDasharray="3 3"
                    label={{
                      value: `Baseline ${fmtUSD(baseline)}`,
                      fill: "#5a6480",
                      fontSize: 10,
                      position: "insideTopRight",
                    }}
                  />
                )}
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="rounded-xl border border-white/10 bg-[#0B0F1E]/95 p-2.5 shadow-2xl backdrop-blur-xl text-xs">
                          <span className="text-text-muted block text-[10px]">
                            {new Date(data.ts).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            })}
                          </span>
                          <span className="num font-bold text-cyan-400 text-sm block mt-0.5">
                            {fmtUSD(data.equity)} USD
                          </span>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#00E5FF"
                  strokeWidth={2.4}
                  fill="url(#equityGrad)"
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
            ) : (
              <div className="h-full w-full flex flex-col items-center justify-center gap-2 text-center">
                <span className="num text-lg font-bold text-white">
                  {currentEquity > 0 ? fmtUSD(currentEquity) : "—"}
                </span>
                <span className="text-[11px] text-text-muted">
                  Live equity — curve accumulates as the desk completes cycles
                </span>
              </div>
            )}
          </div>
        </section>

        {/* Right Hero: Account Loss Analysis */}
        <section
          className="card p-5 lg:col-span-4 flex flex-col justify-between"
          aria-label="Account Loss Analysis"
        >
          <div>
            {/* Header with Segmented Toggle */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BarChart3 size={15} className="text-cyan-400" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-white">
                  Account Loss Analysis
                </h2>
              </div>
              <div className="flex items-center rounded-lg border border-white/5 bg-white/[0.03] p-0.5 text-[10px]">
                <button
                  onClick={() => setLossTab("max")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    lossTab === "max" ? "bg-cyan-500/20 text-cyan-400 font-bold" : "text-text-muted hover:text-white"
                  }`}
                >
                  Max
                </button>
                <button
                  onClick={() => setLossTab("current")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    lossTab === "current" ? "bg-cyan-500/20 text-cyan-400 font-bold" : "text-text-muted hover:text-white"
                  }`}
                >
                  Current
                </button>
              </div>
            </div>

            {/* Gauge 1: Open Risk vs Portfolio Cap (live) */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-text-secondary text-[11.5px]">Open Risk / Portfolio Cap</span>
                <span className="num font-mono text-[11px] text-cyan-400 font-bold">
                  {riskCapPct > 0
                    ? `${Math.min(100, (riskUsedPct / riskCapPct) * 100).toFixed(1)}% of cap`
                    : "—"}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden p-0.5 border border-white/5">
                <div
                  className="h-full rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(0,229,255,0.4)]"
                  style={{
                    width: `${riskCapPct > 0 ? Math.max(2, Math.min(100, (riskUsedPct / riskCapPct) * 100)) : 0}%`,
                  }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] text-text-muted mt-1.5 font-mono">
                <span>Open risk: {currentEquity > 0 ? fmtUSD(openRiskUsd) : "—"}</span>
                <span>Cap: {(riskCapPct * 100).toFixed(0)}% NAV</span>
              </div>
            </div>

            {/* Gauge 2: Daily Loss Limit Level (live halt bound) */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-text-secondary text-[11.5px]">Daily Loss Limit Level</span>
                <span className="num font-mono text-[11px] text-text-secondary font-bold">
                  {dayLossUsedPct.toFixed(1)}% used
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden p-0.5 border border-white/5">
                <div
                  className={`h-full rounded-full transition-all ${
                    dayLossUsedPct > 50 ? "bg-[#FF4D5E]" : "bg-cyan-400"
                  }`}
                  style={{ width: `${Math.max(4, dayLossUsedPct)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] text-text-muted mt-1.5 font-mono">
                <span>Session open: {currentEquity > 0 ? fmtUSD(dayStartEquity) : "—"}</span>
                <span className="text-[#FF4D5E]">
                  Halt: -{currentEquity > 0 ? fmtUSD(dailyHaltLine) : "—"} (-{(haltPct * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
          </div>

          {/* Bottom Countdown Strip — live Alpaca clock */}
          <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 text-text-muted text-[11px]">
              <Clock size={13} className="text-cyan-400" />
              <span>{market?.open ? "Market closes" : market?.phase === "pre" ? "Pre-market — opens in" : "Next market open"}</span>
            </div>
            <span className="num font-mono text-xs font-bold text-white bg-white/5 px-2 py-0.5 rounded border border-white/10">
              {clockValue}
            </span>
          </div>
        </section>
      </div>

      {/* =================================================================== */}
      {/* 2. MIDDLE ROW: 4 Metric Cards (live)                                */}
      {/* =================================================================== */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
        <MetricCard
          label="Day P&L"
          value={kpis ? fmtUSD(dayPnl, true) : "—"}
          sub={kpis ? "Live from Alpaca account" : "Waiting for desk connection"}
          icon={dayPnl >= 0 ? TrendingUp : ArrowDownRight}
          pillText={kpis ? `${dayPnl >= 0 ? "+" : ""}${dayStartEquity > 0 ? ((dayPnl / dayStartEquity) * 100).toFixed(2) : "0.00"}%` : undefined}
          pillPositive={kpis ? dayPnl >= 0 : null}
          sparklineColor={dayPnl >= 0 ? "#00E5FF" : "#FF4D5E"}
          sparklineVariant={dayPnl >= 0 ? "up" : "down"}
        />

        <MetricCard
          label="Total P&L"
          value={kpis ? fmtUSD(kpis.total_pnl, true) : "—"}
          sub={kpis ? `vs ${fmtUSD(baseline)} baseline` : "Waiting for desk connection"}
          icon={kpis && kpis.total_pnl >= 0 ? TrendingUp : ArrowDownRight}
          pillText={kpis ? (kpis.total_pnl >= 0 ? "In profit" : "Drawdown") : undefined}
          pillPositive={kpis ? kpis.total_pnl >= 0 : null}
          sparklineColor={kpis && kpis.total_pnl >= 0 ? "#00FF87" : "#FF4D5E"}
          sparklineVariant={kpis && kpis.total_pnl >= 0 ? "up" : "down"}
        />

        <MetricCard
          label="Open Risk"
          value={kpis ? `${(riskUsedPct * 100).toFixed(2)}% NAV` : "—"}
          sub={kpis ? `${fmtUSD(openRiskUsd)} premium at risk` : "Waiting for desk connection"}
          icon={Gauge}
          pillText={kpis ? `Cap ${(riskCapPct * 100).toFixed(0)}%` : undefined}
          pillPositive={riskCapPct > 0 && riskUsedPct <= riskCapPct ? true : riskCapPct > 0 ? false : null}
          sparklineColor="#38BDF8"
          sparklineVariant="steady"
        />

        <MetricCard
          label="Gate Decisions"
          value={gateTotal > 0 ? `${gatePassed}/${gateTotal}` : "—"}
          sub={gateTotal > 0 ? `${gateRejected} honest rejection${gateRejected === 1 ? "" : "s"} journaled` : "No cycles completed yet"}
          icon={Sparkles}
          pillText={gateTotal > 0 ? "12-gate kernel" : undefined}
          pillPositive={null}
          sparklineColor="#00FF87"
          sparklineVariant="wave"
        />
      </div>

      {/* =================================================================== */}
      {/* 3. DESK DISCIPLINE SECTION (live gate + exit stats)                 */}
      {/* =================================================================== */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2.5">
          <CheckCircle2 size={14} className="text-cyan-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-white">
            Desk Discipline
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          <div className="card p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Position Size Bound</span>
              <span className="pill text-[9.5px] pill-profit">Enforced</span>
            </div>
            <div className="flex items-baseline justify-between text-xs mt-2 pt-2 border-t border-white/5">
              <span className="text-text-muted text-[11px]">Per structure: <strong className="text-white">{(((state?.config_snapshot?.max_position_size_pct as number) ?? 0.01) * 100).toFixed(2)}% NAV</strong></span>
              <span className="num font-bold text-cyan-400">Code gate, not a prompt</span>
            </div>
          </div>

          <div className="card p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Exit Ladder</span>
              <span className="pill text-[9.5px] pill-profit">Armed</span>
            </div>
            <div className="flex items-baseline justify-between text-xs mt-2 pt-2 border-t border-white/5">
              <span className="text-text-muted text-[11px]">TP <strong className="text-white">{(((state?.config_snapshot?.profit_target_pct as number) ?? 0.5) * 100).toFixed(0)}% credit</strong> · Stop <strong className="text-white">{((state?.config_snapshot?.hard_stop_multiple as number) ?? 2).toFixed(1)}×</strong></span>
              <span className="num font-bold text-cyan-400">Runs before entries</span>
            </div>
          </div>

          <div className="card p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Daily Halt</span>
              <span className="pill text-[9.5px] pill-profit">Standing</span>
            </div>
            <div className="flex items-baseline justify-between text-xs mt-2 pt-2 border-t border-white/5">
              <span className="text-text-muted text-[11px]">Flatten at <strong className="text-white">-{(haltPct * 100).toFixed(1)}% NAV</strong></span>
              <span className="num font-bold text-cyan-400">
                {state?.halts?.length ? "Entries halted" : "Not tripped"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* =================================================================== */}
      {/* 4. BOTTOM SPLIT: Open Options Structures + Live Desk Activity Feed  */}
      {/* =================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Open Options Structures (7 cols) */}
        <div className="lg:col-span-7">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <Layers size={14} className="text-cyan-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">
                Open Options Structures
              </h2>
            </div>
            <span className="text-[11px] text-text-muted font-mono">
              Defined Risk · 1% NAV cap
            </span>
          </div>
          <PositionsTable />
        </div>

        {/* The Desk Live Stream (5 cols) */}
        <div className="lg:col-span-5">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              <Activity size={14} className="text-cyan-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-white">
                The Desk Activity Log
              </h2>
            </div>
            <span className="num text-[11px] text-text-muted font-mono">
              {events.length} events
            </span>
          </div>

          <div className="card p-3 flex flex-col justify-between">
            <div className="scroll-thin max-h-[300px] space-y-2 overflow-y-auto pr-1">
              {events.length ? (
                events.slice(0, 20).map((e) => <FeedCard key={e.id} e={e} />)
              ) : (
                <div className="p-6 text-center text-xs text-text-muted">
                  Waiting for the desk&apos;s live market cycle…
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}
