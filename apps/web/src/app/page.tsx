"use client";

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
  ArrowDown,
  ArrowUp,
  Activity,
  Wallet,
  TrendingUp,
  Gauge,
} from "lucide-react";
import Shell from "@/components/shell/Shell";
import { MascotChip } from "@/components/mascots/DeskDock";
import GateGrid from "@/components/GateGrid";
import { useDeskStore } from "@/lib/store";
import { fmtPct, fmtUSD, signClass, structureTag, timeAgo } from "@/lib/format";
import type { JournalEvent } from "@/lib/types";

function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  positive,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  positive?: boolean | null;
}) {
  return (
    <div className="card card-hover p-4 transition-colors">
      <div className="flex items-center justify-between text-text-muted">
        <span className="text-[13px] font-medium">{label}</span>
        <Icon size={16} aria-hidden />
      </div>
      <div className={`num mt-2 text-2xl font-semibold ${positive === null ? "" : positive ? "text-profit" : positive === false ? "text-loss" : ""}`}>
        {value}
      </div>
      {sub && <div className={`num text-xs ${signClass(0.0001)}`}>{sub}</div>}
    </div>
  );
}

function FeedCard({ e }: { e: JournalEvent }) {
  const isGate = e.type === "gate_verdict";
  const isDecision = e.type === "decision_card";
  const approved = e.data.approved;
  return (
    <div className="fade-enter card card-hover p-3 transition-colors" aria-live="polite">
      <div className="flex items-start gap-2">
        <MascotChip agent={e.agent} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="font-semibold">{e.agent === "desk" ? "The Desk" : undefined}</span>
            <span
              className={`pill ${
                e.level === "error"
                  ? "border-loss/40 text-loss"
                  : e.level === "warn"
                    ? "border-warning/40 text-warning"
                    : "border-border-soft text-text-secondary"
              }`}
            >
              {e.type.replace(/_/g, " ")}
            </span>
            {e.symbol && (
              <span className="pill border-border-soft font-mono text-[10px] text-text-primary">
                {e.symbol}
              </span>
            )}
            <span className="ml-auto text-[11px] text-text-muted">{timeAgo(e.ts)}</span>
          </div>
          <p className="mt-1 text-sm text-text-primary">{e.summary}</p>
          {isGate && e.data.results && (
            <div className="mt-2">
              <GateGrid results={e.data.results} />
              {approved === false && (
                <p className="mt-1 text-xs font-semibold text-warning">
                  REJECTED —{" "}
                  {e.data.results.find((r) => !r.passed)?.reason_code ?? "?"}
                </p>
              )}
            </div>
          )}
          {isDecision && e.data.verdict && (
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="pill border-toro/40 text-toro">
                TORO {(e.data.rounds?.[0]?.conviction ?? 0).toFixed(1)}
              </span>
              <span className="pill border-ursa/40 text-ursa">
                URSA {(e.data.rounds?.[1]?.conviction ?? 0).toFixed(1)}
              </span>
              <span className="pill border-verdi/40 text-verdi">
                VERDI: {e.data.verdict.direction} {e.data.verdict.conviction.toFixed(2)}
              </span>
            </div>
          )}
          {e.model && (
            <span className="num mt-1 inline-block text-[10px] text-text-muted">{e.model}</span>
          )}
        </div>
      </div>
    </div>
  );
}

function PositionsTable() {
  const state = useDeskStore((s) => s.state);
  const positions = state?.positions ?? [];
  if (!positions.length) {
    return (
      <div className="card p-6 text-center text-sm text-text-secondary">
        No open positions — the desk is scanning. Next cycle soon.
      </div>
    );
  }
  return (
    <div className="card overflow-x-auto scroll-thin">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border-soft text-left text-xs text-text-muted">
            <th className="px-3 py-2 font-medium">Symbol</th>
            <th className="px-3 py-2 font-medium">Structure</th>
            <th className="px-3 py-2 font-medium">Qty</th>
            <th className="px-3 py-2 font-medium">Entry credit</th>
            <th className="px-3 py-2 font-medium">Mark</th>
            <th className="px-3 py-2 font-medium">Unrealized</th>
            <th className="px-3 py-2 font-medium">DTE</th>
            <th className="px-3 py-2 font-medium">Exit</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p) => (
            <tr key={p.coid} className="border-b border-border-soft/50 hover:bg-card-hover">
              <td className="px-3 py-2 font-mono font-semibold">{p.symbol}</td>
              <td className="px-3 py-2">
                <span className="pill border-border-soft text-text-secondary">
                  {structureTag(p.kind)}
                </span>
              </td>
              <td className="num px-3 py-2">{p.qty}</td>
              <td className="num px-3 py-2">{fmtUSD(p.entry_credit)}</td>
              <td className="num px-3 py-2">{fmtUSD(p.current_mark)}</td>
              <td className={`num px-3 py-2 ${signClass(p.unrealized_pnl)}`}>
                {p.unrealized_pnl >= 0 ? "▲" : "▼"} {fmtUSD(p.unrealized_pnl, true)}
              </td>
              <td className="num px-3 py-2">{p.dte}</td>
              <td className="px-3 py-2 text-xs text-text-secondary">{p.exit_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function OverviewPage() {
  const state = useDeskStore((s) => s.state);
  const events = useDeskStore((s) => s.events);
  const kpis = state?.kpis;
  const curve = (state?.equity_curve ?? []).map((p) => ({
    ts: new Date(p.ts).getTime(),
    equity: p.equity,
  }));
  const narration = events.find((e) => e.type === "narration")?.summary;

  return (
    <Shell>
      <h1 className="mb-4 text-2xl font-bold">Overview</h1>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <KpiCard label="Portfolio Value" value={kpis ? fmtUSD(kpis.portfolio_value) : "—"} icon={Wallet} positive={null} />
        <KpiCard
          label="Today's P&L"
          value={kpis ? fmtUSD(kpis.today_pnl, true) : "—"}
          icon={(kpis?.today_pnl ?? 0) >= 0 ? ArrowUp : ArrowDown}
          positive={kpis ? kpis.today_pnl >= 0 : null}
        />
        <KpiCard
          label="Total P&L"
          value={kpis ? fmtUSD(kpis.total_pnl, true) : "—"}
          icon={TrendingUp}
          positive={kpis ? kpis.total_pnl >= 0 : null}
        />
        <KpiCard
          label="Risk Budget Used"
          value={kpis ? fmtPct(kpis.risk_used_pct, false) : "—"}
          sub={kpis ? `${fmtPct(kpis.open_risk_pct, false)} of NAV at risk` : undefined}
          icon={Gauge}
          positive={null}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-8">
        <section className="card p-4 xl:col-span-5" aria-label="Equity curve">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-base font-semibold">Equity curve</h2>
            <span className="num text-xs text-text-muted">baseline $100,000.00</span>
          </div>
          <div className="h-[280px] min-h-[280px]">
            {curve.length > 1 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={curve} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
                  <defs>
                    <linearGradient id="eq" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4DA3FF" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#4DA3FF" stopOpacity={0.03} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="ts"
                    tickFormatter={(t) => new Date(t).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    stroke="#5E6788"
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis domain={["auto", "auto"]} stroke="#5E6788" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`} />
                  <ReferenceLine y={100000} stroke="#2A3560" strokeDasharray="4 4" />
                  <Tooltip
                    contentStyle={{ background: "#0A0F26", border: "1px solid #2A3560", borderRadius: 10, fontSize: 12 }}
                    labelFormatter={(t) => new Date(Number(t)).toLocaleString()}
                    formatter={(v) => [fmtUSD(Number(v)), "Equity"]}
                  />
                  <Area type="monotone" dataKey="equity" stroke="#4DA3FF" strokeWidth={2} fill="url(#eq)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-text-muted">
                {state ? "Not enough data points yet — the desk just started." : <div className="skeleton h-full w-full" />}
              </div>
            )}
          </div>
        </section>

        <section className="xl:col-span-3" aria-label="The desk">
          <div className="mb-2 flex items-center gap-2">
            <Activity size={16} className="text-info" aria-hidden />
            <h2 className="text-base font-semibold">The Desk</h2>
          </div>
          <div className="scroll-thin flex max-h-[560px] flex-col gap-2 overflow-y-auto pr-1">
            {events.length ? (
              events.map((e) => <FeedCard key={e.id} e={e} />)
            ) : (
              <div className="card p-4 text-sm text-text-secondary">
                Waiting for the desk&apos;s first cycle…
              </div>
            )}
          </div>
          {narration && (
            <p className="mt-2 truncate text-xs text-text-secondary" title={narration}>
              Prime: {narration}
            </p>
          )}
        </section>
      </div>

      <section className="mt-4" aria-label="Positions">
        <h2 className="mb-2 text-base font-semibold">Positions</h2>
        <PositionsTable />
      </section>
    </Shell>
  );
}
