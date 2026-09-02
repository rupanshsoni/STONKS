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
  return (
    <div className="flex flex-wrap items-center gap-1" title={`${passed}/12 gates passed`}>
      {results.map((r) => (
        <span
          key={r.gate}
          title={`${r.gate}: ${r.passed ? "PASS" : `FAIL — ${r.reason_code ?? "?"}`} — ${r.detail}`}
          className={`num inline-flex h-5 w-7 items-center justify-center rounded-[4px] border text-[9px] font-bold ${
            r.passed
              ? "border-profit/30 bg-profit/10 text-profit"
              : "border-loss/40 bg-loss/10 text-loss"
          }`}
        >
          {SHORT[r.gate] ?? "??"}
        </span>
      ))}
      <span
        className={`num ml-1 text-[11px] font-semibold ${
          passed === 12 ? "text-profit" : "text-warning"
        }`}
      >
        {passed === 12 ? "12/12 PASS" : `${passed}/12`}
      </span>
    </div>
  );
}
