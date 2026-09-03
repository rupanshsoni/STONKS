"use client";

import { useState } from "react";
import { CAST, type CastMember } from "@/components/mascots/cast";
import MascotAvatar from "@/components/mascots/MascotAvatar";
import { useDeskStore } from "@/lib/store";
import type { MascotState } from "@/lib/types";
import { Sparkles, Bot, Shield, ChevronRight, X } from "lucide-react";

const PROPS_BY_ID: Record<string, "arms" | "phone" | "horns" | "umbrella" | "gavel" | "clipboard" | "stamp" | "lightbulb"> = {
  prime: "arms",
  senti: "phone",
  toro: "horns",
  ursa: "umbrella",
  verdi: "gavel",
  gate: "clipboard",
  xq: "stamp",
  sage: "lightbulb",
};

function AgentHoverCard({
  member,
  state,
  currentTask,
  lastOutput,
}: {
  member: CastMember;
  state: MascotState;
  currentTask?: string;
  lastOutput?: string;
}) {
  return (
    <div className="absolute right-full mr-3 top-1/2 -translate-y-1/2 w-72 rounded-2xl border border-white/10 bg-[#0B0F1E]/95 p-4 shadow-2xl backdrop-blur-2xl z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-150">
      <div className="flex items-center gap-3 border-b border-white/5 pb-3">
        <div
          className="rounded-xl border p-1 bg-[#060811]"
          style={{ borderColor: `${member.ink}40` }}
        >
          <MascotAvatar
            agent={member.id}
            ink={member.ink}
            prop={PROPS_BY_ID[member.id]}
            state={state}
            size={56}
          />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-1">
            <h4 className="font-semibold text-sm text-white truncate">{member.name}</h4>
            <span
              className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border"
              style={{
                borderColor: `${member.ink}40`,
                backgroundColor: `${member.ink}15`,
                color: member.ink,
              }}
            >
              {state}
            </span>
          </div>
          <p className="text-[11px] text-text-secondary truncate">{member.role}</p>
          <span className="inline-block mt-1 font-mono text-[10px] text-text-muted">
            {member.model}
          </span>
        </div>
      </div>

      <div className="mt-3 space-y-2 text-xs">
        {currentTask ? (
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Current Task</span>
            <p className="text-text-primary text-[12px] leading-snug line-clamp-2 mt-0.5">
              {currentTask}
            </p>
          </div>
        ) : lastOutput ? (
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Latest Output</span>
            <p className="text-text-primary text-[12px] leading-snug line-clamp-2 mt-0.5">
              {lastOutput}
            </p>
          </div>
        ) : (
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wider text-text-muted">Directives</span>
            <p className="text-text-secondary text-[11px] leading-snug mt-0.5">
              {member.description}
            </p>
          </div>
        )}

        <div className="pt-2 border-t border-white/5">
          <p className="italic text-[11px] text-text-muted">
            &ldquo;{member.quip}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
}

export default function RightAgentSidebar({
  open = false,
  onClose,
}: {
  open?: boolean;
  onClose?: () => void;
}) {
  const deskState = useDeskStore((s) => s.state);
  const agentStates = useDeskStore((s) => s.agentStates);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const agentCards = deskState?.agents ?? [];

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm 2xl:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed top-0 right-0 bottom-0 z-40 w-72 flex flex-col border-l border-white/5 bg-[#080B15]/90 backdrop-blur-2xl transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "translate-x-full 2xl:translate-x-0"
        }`}
        aria-label="Trading Desk Agents"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-white/5">
          <div className="flex items-center gap-2">
            <div className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </div>
            <span className="text-xs font-semibold tracking-wider uppercase text-text-primary">
              The Desk
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="pill text-[10px] border-white/10 bg-white/5 text-text-muted">
              8 Agents Live
            </span>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1 rounded-lg hover:bg-white/5 text-text-muted hover:text-white 2xl:hidden"
                aria-label="Close sidebar"
              >
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Agent Roster List */}
        <div className="flex-1 overflow-y-auto scroll-thin px-2 py-3 space-y-1.5">
          {CAST.map((member) => {
            const card = agentCards.find((a) => a.id === member.id);
            const currentState: MascotState =
              agentStates[member.id] ?? card?.state ?? "idle";
            const prop = PROPS_BY_ID[member.id] ?? "arms";
            const isHovered = hoveredId === member.id;

            return (
              <div
                key={member.id}
                className="relative"
                onMouseEnter={() => setHoveredId(member.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <div
                  className={`group flex items-center gap-3 p-2.5 rounded-xl border transition-all duration-200 cursor-pointer ${
                    isHovered
                      ? "border-white/15 bg-white/[0.05] shadow-lg"
                      : "border-transparent hover:border-white/5 hover:bg-white/[0.02]"
                  }`}
                  style={{
                    boxShadow: isHovered ? `0 4px 20px ${member.ink}15` : undefined,
                  }}
                >
                  {/* Mascot Avatar with subtle status halo */}
                  <div
                    className="relative shrink-0 rounded-lg p-0.5 border bg-[#05070E] transition-transform group-hover:scale-105"
                    style={{
                      borderColor: `${member.ink}35`,
                      boxShadow: `0 0 10px ${member.ink}15`,
                    }}
                  >
                    <MascotAvatar
                      agent={member.id}
                      ink={member.ink}
                      prop={prop}
                      state={currentState}
                      size={36}
                      headOnly
                    />
                    {/* Tiny state indicator pip */}
                    <span
                      className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full border border-[#080B15]"
                      style={{
                        backgroundColor:
                          currentState === "idle"
                            ? "#10B981"
                            : currentState === "celebrating"
                            ? "#FBBF24"
                            : currentState === "risk_alert"
                            ? "#EF4444"
                            : member.ink,
                      }}
                    />
                  </div>

                  {/* Name and State description */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-semibold text-text-primary group-hover:text-white truncate">
                        {member.name}
                      </span>
                      <span
                        className="text-[8.5px] font-mono uppercase tracking-wide font-semibold px-1 py-0.5 rounded"
                        style={{
                          color: member.ink,
                          backgroundColor: `${member.ink}15`,
                        }}
                      >
                        {currentState.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-[10px] text-text-muted truncate mt-0.5">
                      {card?.task || member.role}
                    </p>
                  </div>
                </div>

                {/* Hover Flyout Info Card */}
                {isHovered && (
                  <AgentHoverCard
                    member={member}
                    state={currentState}
                    currentTask={card?.task}
                    lastOutput={card?.last_output}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom Desk Snapshot */}
        <div className="p-3 border-t border-white/5 bg-[#05070E]/60">
          <div className="flex items-center justify-between text-[11px] text-text-muted">
            <span className="flex items-center gap-1">
              <Shield size={12} className="text-emerald-400" />
              12 Risk Gates Active
            </span>
            <span className="font-mono text-[10px] text-cyan-400">
              30m cycle
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
