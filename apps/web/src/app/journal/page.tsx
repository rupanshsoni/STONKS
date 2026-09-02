"use client";

import { useEffect, useMemo, useState } from "react";
import Shell from "@/components/shell/Shell";
import { MascotChip } from "@/components/mascots/DeskDock";
import { getJournal } from "@/lib/api";
import { useDeskStore } from "@/lib/store";
import { clockTime, timeAgo } from "@/lib/format";

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
      (a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime(),
    );
  }, [fetched, liveEvents]);

  const filtered = merged.filter(
    (e) =>
      (agent === "all" || e.agent === agent) &&
      (type === "all" || e.type === type) &&
      (!symbol || (e.symbol ?? "").toUpperCase().includes(symbol.toUpperCase())),
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
    a.download = "stonks-journal.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Shell>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Journal</h1>
        <button
          onClick={exportJson}
          className="pill border-border-soft text-text-secondary transition-colors hover:border-info/40 hover:text-info"
        >
          Export journal
        </button>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <select
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
          aria-label="Filter by agent"
          className="rounded-control border border-border-soft bg-card px-2 py-1 text-xs text-text-primary"
        >
          <option value="all">all agents</option>
          {agents.map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          aria-label="Filter by event type"
          className="rounded-control border border-border-soft bg-card px-2 py-1 text-xs text-text-primary"
        >
          <option value="all">all types</option>
          {types.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="symbol…"
          aria-label="Filter by symbol"
          className="num w-28 rounded-control border border-border-soft bg-card px-2 py-1 text-xs text-text-primary placeholder:text-text-muted"
        />
        <span className="num self-center text-xs text-text-muted">
          {filtered.length} events
        </span>
      </div>

      <div className="card overflow-x-auto scroll-thin">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-soft text-left text-xs text-text-muted">
              <th className="px-3 py-2 font-medium">Time</th>
              <th className="px-3 py-2 font-medium">Agent</th>
              <th className="px-3 py-2 font-medium">Type</th>
              <th className="px-3 py-2 font-medium">Symbol</th>
              <th className="px-3 py-2 font-medium">Summary</th>
              <th className="px-3 py-2 font-medium">Surface</th>
              <th className="px-3 py-2 font-medium">Model</th>
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 300).map((e) => (
              <tr key={e.id} className="border-b border-border-soft/50 hover:bg-card-hover">
                <td className="num px-3 py-1.5 text-xs text-text-muted" title={timeAgo(e.ts)}>
                  {clockTime(e.ts)}
                </td>
                <td className="px-3 py-1.5">
                  <MascotChip agent={e.agent} size={22} />
                </td>
                <td className="num px-3 py-1.5 text-xs">{e.type}</td>
                <td className="num px-3 py-1.5 text-xs">{e.symbol ?? "—"}</td>
                <td className="max-w-[420px] truncate px-3 py-1.5 text-xs" title={e.summary}>
                  {e.summary}
                </td>
                <td className="num px-3 py-1.5 text-[10px] uppercase text-text-muted">
                  {e.surface ?? "—"}
                </td>
                <td className="num px-3 py-1.5 text-[10px] text-text-muted">{e.model ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && (
          <p className="p-6 text-center text-sm text-text-secondary">
            No events match the filters.
          </p>
        )}
      </div>
    </Shell>
  );
}
