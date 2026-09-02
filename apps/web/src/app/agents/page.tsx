"use client";

import { useState } from "react";
import Shell from "@/components/shell/Shell";
import MascotAvatar from "@/components/mascots/MascotAvatar";
import { CAST } from "@/components/mascots/cast";
import { useDeskStore } from "@/lib/store";
import { timeAgo } from "@/lib/format";

const PROPS: Record<string, string> = {
  prime: "arms",
  senti: "phone",
  toro: "horns",
  ursa: "umbrella",
  verdi: "gavel",
  gate: "clipboard",
  xq: "stamp",
  sage: "lightbulb",
};

export default function AgentsPage() {
  const state = useDeskStore((s) => s.state);
  const events = useDeskStore((s) => s.events);
  const states = useDeskStore((s) => s.agentStates);
  const [open, setOpen] = useState<string | null>(null);

  const cards = state?.agents ?? [];

  return (
    <Shell>
      <h1 className="mb-4 text-2xl font-bold">Agents</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {CAST.map((c) => {
          const card = cards.find((a) => a.id === c.id);
          const timeline = events.filter((e) => e.agent === c.id).slice(0, 20);
          const isOpen = open === c.id;
          return (
            <div key={c.id} className={`card card-hover p-4 transition-colors ${isOpen ? "md:col-span-2 xl:col-span-4" : ""}`}>
              <button
                className="flex w-full items-start gap-3 text-left"
                onClick={() => setOpen(isOpen ? null : c.id)}
              >
                <span
                  className={`mascot-state-${states[c.id] ?? card?.state ?? "idle"} rounded-xl ring-2 ring-offset-2 ring-offset-page`}
                  style={{ ["--tw-ring-color" as string]: c.ink }}
                >
                  <MascotAvatar
                    agent={c.id}
                    ink={c.ink}
                    prop={PROPS[c.id] as "arms"}
                    size={96}
                  />
                </span>
                <div className="min-w-0 flex-1">
                  <h2 className="font-semibold" style={{ color: c.ink }}>
                    {c.name}
                  </h2>
                  <p className="text-xs text-text-secondary">{c.role}</p>
                  <span
                    className={`pill mt-2 ${
                      card?.state && card.state !== "idle"
                        ? "border-info/40 bg-info/10 text-info"
                        : "border-border-soft text-text-muted"
                    }`}
                  >
                    {states[c.id] ?? card?.state ?? "idle"}
                  </span>
                  <p className="mt-2 line-clamp-2 text-xs text-text-secondary">
                    {card?.task || card?.last_output || c.quip}
                  </p>
                  {card?.model && (
                    <span className="num mt-1 inline-block text-[10px] text-text-muted">
                      {card.model}
                    </span>
                  )}
                </div>
              </button>

              {isOpen && (
                <div className="mt-4 border-t border-border-soft pt-3">
                  <h3 className="mb-2 text-sm font-semibold">Recent actions</h3>
                  {timeline.length ? (
                    <ul className="scroll-thin max-h-64 space-y-1 overflow-y-auto">
                      {timeline.map((e) => (
                        <li key={e.id} className="flex items-baseline gap-2 text-xs">
                          <span className="num shrink-0 text-text-muted">{timeAgo(e.ts)}</span>
                          <span className="text-text-secondary">{e.summary}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-text-muted">No recorded actions yet.</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Shell>
  );
}
