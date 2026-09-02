"use client";

import { create } from "zustand";
import type { AgentId, DeskState, JournalEvent, MascotState } from "./types";

const STATE_BY_TYPE: Record<string, MascotState> = {
  cycle_start: "idle",
  cycle_end: "idle",
  analysis: "analyzing",
  senti_report: "reading_news",
  debate_round: "debating",
  debate_verdict: "debating",
  gate_verdict: "idle",
  rejected_proposal: "risk_alert",
  order_submitted: "trading",
  order_working: "trading",
  order_filled: "celebrating",
  exit_rule: "trading",
  position_closed: "celebrating",
  post_mortem: "post_mortem",
  lesson_learned: "post_mortem",
  narration: "idle",
  market_closed: "sleeping",
  reconcile: "idle",
  ask_received: "analyzing",
  decision_card: "idle",
  error: "risk_alert",
  equity_tick: "idle",
};

interface DeskStore {
  state: DeskState | null;
  events: JournalEvent[];
  agentStates: Record<string, MascotState>;
  connected: boolean;
  glitchFlash: number;
  setState: (s: DeskState) => void;
  applyEvent: (e: JournalEvent) => void;
  setConnected: (c: boolean) => void;
}

export const useDeskStore = create<DeskStore>((set, get) => ({
  state: null,
  events: [],
  agentStates: {},
  connected: false,
  glitchFlash: 0,
  setState: (s) => set({ state: s }),
  applyEvent: (e) =>
    set((st) => {
      const events = [e, ...st.events].slice(0, 300);
      const agentStates = { ...st.agentStates };
      const mascot =
        (e.data.mascot_state as MascotState | undefined) ??
        STATE_BY_TYPE[e.type];
      if (mascot && e.agent !== "desk") {
        agentStates[e.agent] = mascot;
      }
      if (e.type === "market_closed") {
        for (const a of ["prime", "senti", "toro", "ursa", "verdi", "gate", "xq", "sage"]) {
          agentStates[a] = "sleeping";
        }
      }
      if (e.type === "gate_verdict" && e.agent === "gate") {
        agentStates.gate = e.data.approved ? "idle" : "risk_alert";
      }
      const glitchFlash =
        e.type === "order_filled" ? st.glitchFlash + 1 : st.glitchFlash;
      return { events, agentStates, glitchFlash };
    }),
  setConnected: (c) => set({ connected: c }),
}));

export function useAgentState(id: AgentId): MascotState {
  return useDeskStore((s) => s.agentStates[id] ?? "idle");
}
