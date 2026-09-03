"use client";

import { useDeskStore } from "@/lib/store";
import { fmtUSD, signClass } from "@/lib/format";
import { Search, Radio, Bell, Users, ShieldAlert } from "lucide-react";

export default function TopBar({
  onToggleAgents,
}: {
  onToggleAgents?: () => void;
}) {
  const state = useDeskStore((s) => s.state);
  const connected = useDeskStore((s) => s.connected);
  const glitchFlash = useDeskStore((s) => s.glitchFlash);

  const kpis = state?.kpis;
  const account = state?.account;
  const isMarketOpen = state?.market.open;

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-white/5 bg-[#06080d]/85 px-4 py-3 backdrop-blur-2xl lg:pl-60 2xl:pr-76">
      {/* Search / Status Command Area */}
      <div className="flex items-center gap-3">
        <span
          key={glitchFlash}
          className="stonks-wordmark text-sm font-extrabold text-white pl-10 lg:pl-0"
          data-text="STONKS"
        >
          STONKS DESK
        </span>
        <div className="hidden sm:flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-1.5 text-xs text-text-muted">
          <Search size={14} className="text-text-muted" />
          <span className="text-[11px]">Options Chain · 30m Autonomous Cycle</span>
        </div>
      </div>

      {/* Right KPI & Status Section */}
      <div className="flex items-center gap-3 text-xs sm:gap-4">
        {/* Quick KPI stats */}
        {kpis && (
          <div className="hidden md:flex flex-col items-end">
            <span className="num text-sm font-bold text-white tracking-tight">
              {fmtUSD(kpis.portfolio_value)}
            </span>
            <span
              className={`num text-[11px] font-semibold ${signClass(
                kpis.today_pnl
              )}`}
            >
              {kpis.today_pnl >= 0 ? "+" : ""}
              {fmtUSD(kpis.today_pnl, true)} (today)
            </span>
          </div>
        )}

        {/* Market Status Radar */}
        <div
          className={`inline-flex h-[26px] items-center gap-1.5 rounded-full border px-2.5 text-[11px] font-semibold leading-none ${
            isMarketOpen
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
              : "border-white/10 bg-white/5 text-text-muted"
          }`}
        >
          <span
            className={`h-1.5 w-1.5 shrink-0 rounded-full ${
              isMarketOpen ? "bg-emerald-400 animate-pulse shadow-[0_0_8px_#00ff87]" : "bg-neutral-500"
            }`}
          />
          <span className="leading-none">{isMarketOpen ? "MARKET OPEN" : "MARKET CLOSED"}</span>
        </div>

        {/* Paper Account Badge */}
        <div className="hidden sm:inline-flex h-[26px] items-center gap-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 font-mono text-[10.5px] font-semibold text-cyan-400 leading-none">
          <Radio size={11} className="shrink-0 text-cyan-400" />
          <span className="leading-none">PAPER · {account?.account_number ?? "ACCT-01"}</span>
        </div>

        {/* SSE Stream Health Status */}
        <div
          className="flex items-center gap-1 text-[11px] text-text-muted"
          title={connected ? "Live SSE Stream Active" : "Reconnecting to stream..."}
        >
          <span
            className={`h-2 w-2 rounded-full transition-colors ${
              connected ? "bg-emerald-400 shadow-[0_0_8px_#00ff87]" : "bg-red-500"
            }`}
          />
        </div>

        {/* Toggle Right Agents Sidebar on smaller screens */}
        {onToggleAgents && (
          <button
            onClick={onToggleAgents}
            className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.04] px-2.5 py-1.5 text-xs text-text-secondary hover:text-white hover:bg-white/[0.08] 2xl:hidden"
            aria-label="Toggle agent sidebar"
          >
            <Users size={15} />
            <span className="hidden sm:inline text-[11px]">The Desk</span>
          </button>
        )}
      </div>
    </header>
  );
}
