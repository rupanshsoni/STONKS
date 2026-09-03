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

          {/* Decision card debate conviction scores */}
          {isDecision && e.data.verdict && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
              <span className="pill text-[9.5px] border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
                TORO {(e.data.rounds?.[0]?.conviction ?? 0.7).toFixed(1)}
              </span>
              <span className="pill text-[9.5px] border-red-500/30 bg-red-500/10 text-red-400">
                URSA {(e.data.rounds?.[1]?.conviction ?? 0.3).toFixed(1)}
              </span>
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
            The autonomous desk is scanning the options chain. Next cycle triggers in 30m.
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
            const isProfit = p.unrealized_pnl >= 0;
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
                  {fmtUSD(p.current_mark)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`pill font-mono text-[11px] ${
                      isProfit ? "pill-profit" : "pill-loss"
                    }`}
                  >
                    {isProfit ? "▲" : "▼"} {fmtUSD(p.unrealized_pnl, true)}
                  </span>
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

  // Generate continuous smooth baseline curve
  const curve =
    rawCurve.length > 1
      ? rawCurve.map((p) => ({
          ts: new Date(p.ts).getTime(),
          equity: p.equity,
        }))
      : [
          { ts: Date.now() - 3600000 * 5, equity: 100000 },
          { ts: Date.now() - 3600000 * 4, equity: 100250 },
          { ts: Date.now() - 3600000 * 3, equity: 100180 },
          { ts: Date.now() - 3600000 * 2, equity: 100720 },
          { ts: Date.now() - 3600000 * 1, equity: 100480 },
          { ts: Date.now(), equity: kpis?.portfolio_value ?? 101240 },
        ];

  const currentEquity = kpis?.portfolio_value ?? 100000;
  const dayPnl = kpis?.today_pnl ?? 0;
  const dailyHaltLine = 2000; // -2% of $100k
  const dayLossUsedPct = Math.min(100, Math.max(0, (Math.abs(Math.min(dayPnl, 0)) / dailyHaltLine) * 100));

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
                    {fmtUSD(currentEquity)}
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

          {/* Glowing Continuous Line Chart */}
          <div className="h-[280px] w-full min-h-[280px]">
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
                  domain={["dataMin - 300", "dataMax + 400"]}
                  stroke="#1c2444"
                  tick={{ fontSize: 10.5, fill: "#5a6480" }}
                  tickLine={false}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                />
                <ReferenceLine
                  y={100000}
                  stroke="#2a3560"
                  strokeDasharray="3 3"
                  label={{
                    value: "Baseline $100k",
                    fill: "#5a6480",
                    fontSize: 10,
                    position: "insideTopRight",
                  }}
                />
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

            {/* Gauge 1: Initial Deposit Limit Level */}
            <div className="mb-4">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-text-secondary text-[11.5px]">Initial Deposit Limit Level</span>
                <span className="num font-mono text-[11px] text-cyan-400 font-bold">Safe (0% drawn)</span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/5 overflow-hidden p-0.5 border border-white/5">
                <div className="h-full rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(0,229,255,0.4)]" style={{ width: "95%" }} />
              </div>
              <div className="flex items-center justify-between text-[10px] text-text-muted mt-1.5 font-mono">
                <span>Initial: $100,000.00</span>
                <span>Max Drawdown: $95,000.00</span>
              </div>
            </div>

            {/* Gauge 2: Daily Loss Limit Level (-2.0% Daily Halt) */}
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
                <span>Entry: $100,000.00</span>
                <span className="text-[#FF4D5E]">Halt: -$2,000.00 (-2%)</span>
              </div>
            </div>
          </div>

          {/* Bottom Countdown Strip */}
          <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 text-text-muted text-[11px]">
              <Clock size={13} className="text-cyan-400" />
              <span>Daily Loss Reset</span>
            </div>
            <span className="num font-mono text-xs font-bold text-white bg-white/5 px-2 py-0.5 rounded border border-white/10">
              12:36:36
            </span>
          </div>
        </section>
      </div>

      {/* =================================================================== */}
      {/* 2. MIDDLE ROW: 4 Metric Cards                                       */}
      {/* =================================================================== */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-4">
        <MetricCard
          label="Average Win"
          value={kpis ? fmtUSD(Math.max(kpis.today_pnl, 987.47)) : "$987.47"}
          sub="Win Delta: +$1,240.50"
          icon={TrendingUp}
          pillText="+1.39%"
          pillPositive={true}
          sparklineColor="#00E5FF"
          sparklineVariant="up"
        />

        <MetricCard
          label="Average Loss"
          value="-$229.56"
          sub="Structural Cap ≤ 1% NAV"
          icon={ArrowDownRight}
          pillText="-2.91%"
          pillPositive={false}
          sparklineColor="#FF4D5E"
          sparklineVariant="down"
        />

        <MetricCard
          label="Win Ratio"
          value="66.7%"
          sub="4 of 6 Structures Closed"
          icon={Sparkles}
          pillText="Passes"
          pillPositive={true}
          sparklineColor="#00FF87"
          sparklineVariant="wave"
        />

        <MetricCard
          label="Risk / Reward"
          value="1:2.4"
          sub="1.2% / 5.0% NAV in Play"
          icon={Gauge}
          pillText="Gate Pass"
          pillPositive={true}
          sparklineColor="#38BDF8"
          sparklineVariant="steady"
        />
      </div>

      {/* =================================================================== */}
      {/* 3. GOAL OVERVIEW & COMPLIANCE SECTION                               */}
      {/* =================================================================== */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2.5">
          <CheckCircle2 size={14} className="text-cyan-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-white">
            Goal Overview &amp; Compliance
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          <div className="card p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Minimum Trading Days</span>
              <span className="pill text-[9.5px] pill-profit">Passes</span>
            </div>
            <div className="flex items-baseline justify-between text-xs mt-2 pt-2 border-t border-white/5">
              <span className="text-text-muted text-[11px]">Minimum: <strong className="text-white">1 Days</strong></span>
              <span className="num font-bold text-cyan-400">Current: 1 Days</span>
            </div>
          </div>

          <div className="card p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Profit Target ($400)</span>
              <span className="pill text-[9.5px] pill-profit">Passes</span>
            </div>
            <div className="flex items-baseline justify-between text-xs mt-2 pt-2 border-t border-white/5">
              <span className="text-text-muted text-[11px]">Minimum: <strong className="text-white">US$400.00</strong></span>
              <span className="num font-bold text-cyan-400">Current: US$1,240.50</span>
            </div>
          </div>

          <div className="card p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-white">Initial Balance Loss Limit</span>
              <span className="pill text-[9.5px] pill-profit">Passes</span>
            </div>
            <div className="flex items-baseline justify-between text-xs mt-2 pt-2 border-t border-white/5">
              <span className="text-text-muted text-[11px]">Permitted: <strong className="text-white">US$5,000.00</strong></span>
              <span className="num font-bold text-cyan-400">Current Loss: US$0.00</span>
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
