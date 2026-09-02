"use client";

import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import DeskDock from "@/components/mascots/DeskDock";
import { useDeskStore } from "@/lib/store";

export default function Shell({ children }: { children: React.ReactNode }) {
  const connected = useDeskStore((s) => s.connected);
  return (
    <div className="min-h-dvh">
      <Sidebar />
      <TopBar />
      {!connected && (
        <div className="border-b border-warning/30 bg-warning/10 px-4 py-2 text-center text-xs text-warning lg:pl-56">
          Quote stream disconnected — retrying. Orders continue; marks may be stale.
        </div>
      )}
      <main className="px-4 py-6 lg:pl-56">{children}</main>
      <DeskDock />
      <footer className="border-t border-border-soft px-4 py-6 text-center text-xs text-text-muted lg:pl-56">
        Strategic Trading &amp; Orchestration Network for Knowledge-driven Systems —
        paper trading only, for the Alpaca AI Trading Agents Hackathon.
      </footer>
    </div>
  );
}
