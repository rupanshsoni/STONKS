"use client";

import { useState } from "react";
import Shell from "@/components/shell/Shell";
import MascotAvatar from "@/components/mascots/MascotAvatar";
import { CAST } from "@/components/mascots/cast";
import { useDeskStore } from "@/lib/store";
import { timeAgo } from "@/lib/format";
import type { MascotState } from "@/lib/types";
import { Bot, Sparkles, Activity, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";

const PROPS: Record<string, "arms" | "phone" | "horns" | "umbrella" | "gavel" | "clipboard" | "stamp" | "lightbulb"> = {
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
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            The Agent Roster
            <span className="pill text-[10px] border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
              {CAST.length} Agents
            </span>
          </h1>
          <p className="text-xs md:text-sm text-text-secondary mt-1">
            Specialized LLM and code agents collaborating to research, deliberate, score, and execute options trades.
          </p>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {CAST.map((c) => {
          const card = cards.find((a) => a.id === c.id);
          const timeline = events.filter((e) => e.agent === c.id).slice(0, 15);
          const isOpen = open === c.id;
          const currentState: MascotState =
            states[c.id] ?? card?.state ?? "idle";

          return (
            <div
              key={c.id}
              className={`card card-hover p-5 flex flex-col justify-between transition-all duration-200 ${
                isOpen ? "md:col-span-2 xl:col-span-4 border-cyan-500/30 shadow-[0_0_30px_rgba(0,229,255,0.06)]" : ""
              }`}
            >
              <div>
                {/* Top Bar: Mascot Avatar & Info */}
                <div className="flex items-start gap-4">
                  <div
                    className="relative shrink-0 rounded-2xl border p-1 bg-[#070a14] shadow-lg"
                    style={{
                      borderColor: `${c.ink}40`,
                      boxShadow: `0 0 20px ${c.ink}15`,
                    }}
                  >
                    <MascotAvatar
                      agent={c.id}
                      ink={c.ink}
                      prop={PROPS[c.id]}
                      state={currentState}
                      size={72}
                    />
                    <span
                      className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-[#0D111C]"
                      style={{
                        backgroundColor:
                          currentState === "idle"
                            ? "#10B981"
                            : currentState === "celebrating"
                            ? "#FBBF24"
                            : currentState === "risk_alert"
                            ? "#EF4444"
                            : c.ink,
                      }}
                    />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <h2 className="font-bold text-base text-white truncate">
                        {c.name}
                      </h2>
                      <span
                        className="text-[9px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold"
                        style={{
                          color: c.ink,
                          backgroundColor: `${c.ink}15`,
                        }}
                      >
                        {currentState}
                      </span>
                    </div>

                    <p className="text-xs text-text-secondary truncate mt-0.5 font-medium">
                      {c.role}
                    </p>

                    <div className="mt-2 flex items-center gap-1.5">
                      <span className="pill font-mono text-[9px] border-white/10 bg-white/5 text-text-muted">
                        {card?.model ?? c.model}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Directives / Current Task */}
                <div className="mt-4 rounded-xl border border-white/5 bg-[#080B15] p-3 text-xs">
                  <div className="text-[10px] font-medium uppercase tracking-wider text-text-muted mb-1 flex items-center gap-1">
                    <Activity size={12} className="text-cyan-400" />
                    {card?.task ? "Active Task" : "Core Directive"}
                  </div>
                  <p className="text-text-primary text-[12px] leading-relaxed line-clamp-2">
                    {card?.task || card?.last_output || c.description}
                  </p>
                </div>

                {/* Quip */}
                <p className="mt-3 text-[11px] italic text-text-muted">
                  &ldquo;{c.quip}&rdquo;
                </p>
              </div>

              {/* Action History Toggle Button */}
              <div className="mt-4 pt-3 border-t border-white/5">
                <button
                  onClick={() => setOpen(isOpen ? null : c.id)}
                  className="w-full flex items-center justify-between text-xs text-text-secondary hover:text-white transition-colors"
                >
                  <span className="font-medium">
                    {isOpen ? "Hide Action History" : `View Activity (${timeline.length})`}
                  </span>
                  {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                {/* Expanded Activity Timeline */}
                {isOpen && (
                  <div className="mt-3 pt-2 border-t border-white/5">
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                      Recent Desk Operations
                    </h3>
                    {timeline.length ? (
                      <ul className="scroll-thin max-h-56 space-y-2 overflow-y-auto pr-1">
                        {timeline.map((e) => (
                          <li
                            key={e.id}
                            className="flex items-start gap-2.5 rounded-lg border border-white/5 bg-[#080B15]/60 p-2 text-xs"
                          >
                            <span className="num shrink-0 text-[10px] text-text-muted mt-0.5">
                              {timeAgo(e.ts)}
                            </span>
                            <span className="text-text-primary text-[12px] leading-snug">
                              {e.summary}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-text-muted py-2">
                        No recorded actions yet for this cycle.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Shell>
  );
}
