"use client";

import { useState } from "react";
import MascotAvatar from "./MascotAvatar";
import { CAST, castById } from "./cast";
import { useDeskStore } from "@/lib/store";

export default function DeskDock() {
  const states = useDeskStore((s) => s.agentStates);
  const events = useDeskStore((s) => s.events);
  const [quip, setQuip] = useState<string | null>(null);

  const caption =
    events.find((e) => e.type === "narration")?.summary ??
    events[0]?.summary ??
    "The desk is open.";

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-40 hidden xl:block">
      <div className="pointer-events-auto card p-3">
        <div className="flex items-end gap-1">
          {CAST.map((c) => {
            const isPrime = c.id === "prime";
            return (
              <button
                key={c.id}
                onClick={() => setQuip(c.quip)}
                className={`mascot-state-${states[c.id] ?? "idle"} cursor-pointer rounded transition-transform hover:scale-105 focus-visible:ring-2 focus-visible:ring-verdi focus-visible:outline-none`}
                aria-label={`${c.name}: ${c.quip}`}
                title={c.name}
              >
                <MascotAvatar
                  agent={c.id}
                  ink={c.ink}
                  prop={
                    c.id === "prime" ? "arms" :
                    c.id === "senti" ? "phone" :
                    c.id === "toro" ? "horns" :
                    c.id === "ursa" ? "umbrella" :
                    c.id === "verdi" ? "gavel" :
                    c.id === "gate" ? "clipboard" :
                    c.id === "xq" ? "stamp" : "lightbulb"
                  }
                  size={isPrime ? 104 : 72}
                />
              </button>
            );
          })}
        </div>
        <p className="mt-1 max-w-[560px] truncate text-left text-xs text-text-secondary">
          <span className="text-prime font-semibold">Prime:</span> {quip ?? caption}
        </p>
      </div>
    </div>
  );
}

export function MascotChip({ agent, size = 28 }: { agent: string; size?: number }) {
  const member = castById(agent);
  if (!member) {
    return (
      <span
        className="inline-flex items-center justify-center rounded-full border border-border-soft bg-card text-[10px] font-bold text-text-secondary"
        style={{ width: size, height: size }}
      >
        D
      </span>
    );
  }
  return (
    <span
      className="mascot-state-idle inline-flex items-center justify-center overflow-hidden rounded-full border"
      style={{ width: size, height: size, borderColor: member.ink }}
    >
      <MascotAvatar
        agent={member.id}
        ink={member.ink}
        prop={
          member.id === "prime" ? "arms" :
          member.id === "senti" ? "phone" :
          member.id === "toro" ? "horns" :
          member.id === "ursa" ? "umbrella" :
          member.id === "verdi" ? "gavel" :
          member.id === "gate" ? "clipboard" :
          member.id === "xq" ? "stamp" : "lightbulb"
        }
        size={size}
        headOnly
      />
    </span>
  );
}
