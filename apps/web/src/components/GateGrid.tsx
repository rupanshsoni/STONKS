"use client";

import type { GateResult } from "@/lib/types";

const SHORT: Record<string, string> = {
  SANITY: "SY",
  REGIME: "RG",
  VRP_EDGE: "VR",
  EVENT_RISK: "EV",
  DEFINED_RISK: "DR",
  LIQUIDITY: "LQ",
  CREDIT_QUALITY: "CQ",
  POSITION_SIZE: "PS",
  PORTFOLIO_RISK: "PR",
  CONCENTRATION: "CN",
  DUPLICATE: "DP",
  DAILY_HALT: "DH",
};

export default function GateGrid({ results }: { results: GateResult[] }) {
  const passed = results.filter((r) => r.passed).length;
  const isAllPassed = passed === 12;

  return (
    <div className="flex flex-wrap items-center gap-1.5" title={`${passed}/12 gates passed`}>
      <div className="flex flex-wrap items-center gap-1">
        {results.map((r) => (
          <span
            key={r.gate}
            title={`${r.gate}: ${r.passed ? "PASSED" : `FAILED (${r.reason_code ?? "?"})`} — ${r.detail}`}
            className={`num inline-flex h-5 w-7 items-center justify-center rounded-md border text-[9px] font-bold tracking-tight transition-all duration-150 hover:scale-110 ${
              r.passed
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.15)]"
                : "border-red-500/40 bg-red-500/10 text-red-400 shadow-[0_0_8px_rgba(239,68,68,0.2)]"
            }`}
          >
            {SHORT[r.gate] ?? "??"}
          </span>
        ))}
      </div>
      <span
        className={`num text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
          isAllPassed
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            : "border-amber-500/30 bg-amber-500/10 text-amber-400"
        }`}
      >
        {isAllPassed ? "12/12 PASS" : `${passed}/12 GATES`}
      </span>
    </div>
  );
}
