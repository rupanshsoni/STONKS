"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import RightAgentSidebar from "./RightAgentSidebar";
import { useDeskStore } from "@/lib/store";

export default function Shell({ children }: { children: React.ReactNode }) {
  const connected = useDeskStore((s) => s.connected);
  const [agentsDrawerOpen, setAgentsDrawerOpen] = useState(false);

  return (
    <div className="min-h-dvh flex flex-col bg-[#06080d] text-text-primary selection:bg-cyan-500/20">
      {/* Left Navigation Sidebar */}
      <Sidebar />

      {/* Top Header Bar */}
      <TopBar onToggleAgents={() => setAgentsDrawerOpen((prev) => !prev)} />

      {/* Disconnected Stream Warning Banner */}
      {!connected && (
        <div className="border-b border-amber-500/30 bg-amber-500/10 px-4 py-2 text-center text-xs font-medium text-amber-400 lg:pl-60 2xl:pr-76">
          Quote stream disconnected — auto-reconnecting. Active positions and risk gates remain protected.
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 px-4 py-6 md:px-6 md:py-8 lg:pl-60 2xl:pr-76 max-w-[1780px] w-full mx-auto">
        {children}
      </main>

      {/* Right Trading Desk Agents Sidebar */}
      <RightAgentSidebar
        open={agentsDrawerOpen}
        onClose={() => setAgentsDrawerOpen(false)}
      />

      {/* App Footer */}
      <footer className="border-t border-white/5 px-6 py-5 text-center text-xs text-text-muted lg:pl-60 2xl:pr-76">
        <p className="max-w-xl mx-auto leading-relaxed">
          Strategic Trading &amp; Orchestration Network for Knowledge-driven Systems —
          Autonomous defined-risk options desk executing on Alpaca paper trading.
        </p>
      </footer>
    </div>
  );
}
