"use client";

import { useDeskStore } from "@/lib/store";
import { fmtUSD, signClass } from "@/lib/format";

export default function TopBar() {
  const state = useDeskStore((s) => s.state);
  const connected = useDeskStore((s) => s.connected);
  const glitchFlash = useDeskStore((s) => s.glitchFlash);

  const kpis = state?.kpis;
  const account = state?.account;

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-border-soft bg-page/90 px-4 py-3 backdrop-blur lg:pl-56">
      <span
        key={glitchFlash}
        className="stonks-wordmark pl-8 text-base text-text-primary lg:pl-0"
        data-text="STONKS"
      >
        STONKS
      </span>

      <div className="flex items-center gap-3 text-xs sm:gap-4">
        <div className="hidden sm:block">
          <div className="num text-sm font-semibold">
            {kpis ? fmtUSD(kpis.portfolio_value) : "—"}
          </div>
          <div className={`num text-[11px] ${signClass(kpis?.today_pnl ?? 0)}`}>
            today {kpis ? fmtUSD(kpis.today_pnl, true) : "—"}
          </div>
        </div>

        <span
          className={`pill ${
            state?.market.open
              ? "border-profit/40 bg-profit/10 text-profit"
              : "border-border-soft bg-card text-text-muted"
          }`}
        >
          {state?.market.open ? "OPEN" : "CLOSED"}
        </span>

        <span className="pill border-info/40 bg-info/10 font-mono text-[10px] text-info">
          PAPER · {account?.account_number ?? "ACCT-…"}
        </span>

        <span
          className={`inline-block h-2.5 w-2.5 rounded-full ${
            connected ? "bg-profit" : "bg-loss"
          }`}
          title={connected ? "Live — SSE connected" : "Reconnecting…"}
          role="status"
        />
      </div>
    </header>
  );
}
