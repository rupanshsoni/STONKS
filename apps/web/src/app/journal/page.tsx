"use client";

import { useEffect, useMemo, useState } from "react";
import Shell from "@/components/shell/Shell";
import { MascotChip } from "@/components/mascots/MascotAvatar";
import { getJournal } from "@/lib/api";
import { useDeskStore } from "@/lib/store";
import { clockTime, timeAgo } from "@/lib/format";
import { Download, Filter, Search, ScrollText } from "lucide-react";

export default function JournalPage() {
  const liveEvents = useDeskStore((s) => s.events);
  const [fetched, setFetched] = useState<typeof liveEvents>([]);
  const [agent, setAgent] = useState("all");
  const [type, setType] = useState("all");
  const [symbol, setSymbol] = useState("");

  useEffect(() => {
    getJournal(500).then((rows) => setFetched(rows));
  }, [liveEvents.length === 0]);

  const merged = useMemo(() => {
    const map = new Map<string, (typeof liveEvents)[number]>();
    for (const e of fetched) map.set(e.id, e);
    for (const e of liveEvents) map.set(e.id, e);
    return [...map.values()].sort(
      (a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime()
    );
  }, [fetched, liveEvents]);

  const filtered = merged.filter(
    (e) =>
      (agent === "all" || e.agent === agent) &&
      (type === "all" || e.type === type) &&
      (!symbol || (e.symbol ?? "").toUpperCase().includes(symbol.toUpperCase()))
  );

  const agents = [...new Set(merged.map((e) => e.agent))];
  const types = [...new Set(merged.map((e) => e.type))];

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `stonks-journal-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Shell>
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Forensic Audit Journal
            <span className="pill text-[10px] border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
              Immutable Log
            </span>
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1">
            Complete append-only audit trail: every debate round, sentiment extraction, 12-gate evaluation, order execution, and Alpaca fill.
          </p>
        </div>

        <button
          onClick={exportJson}
          className="flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-semibold text-cyan-400 hover:bg-cyan-500/20 active:scale-95 transition-all"
        >
          <Download size={14} />
          <span>Export Journal JSON</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="card p-3 mb-5 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-xs text-text-muted pl-1">
          <Filter size={14} className="text-cyan-400" />
          <span>Filter:</span>
        </div>

        <select
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
          aria-label="Filter by agent"
          className="rounded-lg border border-white/10 bg-[#080B15] px-3 py-1.5 text-xs text-white focus:border-cyan-400 focus:outline-none"
        >
          <option value="all">All Agents ({agents.length})</option>
          {agents.map((a) => (
            <option key={a} value={a}>
              {a.toUpperCase()}
            </option>
          ))}
        </select>

        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          aria-label="Filter by event type"
          className="rounded-lg border border-white/10 bg-[#080B15] px-3 py-1.5 text-xs text-white focus:border-cyan-400 focus:outline-none"
        >
          <option value="all">All Event Types ({types.length})</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {t.replace(/_/g, " ")}
            </option>
          ))}
        </select>

        <div className="relative">
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="Search ticker..."
            aria-label="Filter by symbol"
            className="w-32 rounded-lg border border-white/10 bg-[#080B15] px-3 py-1.5 text-xs text-white placeholder:text-text-muted focus:border-cyan-400 focus:outline-none font-mono uppercase"
          />
        </div>

        <span className="num ml-auto text-xs text-text-muted pr-1">
          Showing <strong>{filtered.length}</strong> events
        </span>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto scroll-thin">
        <table className="w-full text-left text-xs whitespace-nowrap">
          <thead>
            <tr className="border-b border-white/5 bg-white/[0.02] font-semibold uppercase tracking-wider text-text-muted">
              <th className="px-4 py-3">Time</th>
              <th className="px-4 py-3">Agent</th>
              <th className="px-4 py-3">Event Type</th>
              <th className="px-4 py-3">Ticker</th>
              <th className="px-4 py-3">Summary Description</th>
              <th className="px-4 py-3">Surface</th>
              <th className="px-4 py-3">Model</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.slice(0, 300).map((e) => (
              <tr key={e.id} className="hover:bg-white/[0.02] transition-colors">
                <td
                  className="num px-4 py-2.5 text-text-muted font-mono"
                  title={timeAgo(e.ts)}
                >
                  {clockTime(e.ts)}
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <MascotChip agent={e.agent} size={22} />
                    <span className="font-semibold text-white">
                      {e.agent.toUpperCase()}
                    </span>
                  </div>
                </td>
                <td className="num px-4 py-2.5 font-mono text-[11px]">
                  <span className="pill text-[10px] uppercase border-white/10 bg-white/5 text-text-secondary">
                    {e.type.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="num px-4 py-2.5 font-mono font-bold text-cyan-400">
                  {e.symbol ?? "—"}
                </td>
                <td
                  className="max-w-[460px] truncate px-4 py-2.5 text-text-primary"
                  title={e.summary}
                >
                  {e.summary}
                </td>
                <td className="num px-4 py-2.5 font-mono uppercase text-[10px] text-text-muted">
                  {e.surface ? (
                    <span className="pill text-[9px] border-cyan-500/20 text-cyan-400">
                      {e.surface}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="num px-4 py-2.5 font-mono text-[10px] text-text-muted">
                  {e.model ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!filtered.length && (
          <div className="p-8 text-center text-xs text-text-secondary">
            No events match the active filters.
          </div>
        )}
      </div>
    </Shell>
  );
}
