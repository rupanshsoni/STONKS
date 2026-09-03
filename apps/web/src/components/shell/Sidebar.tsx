"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  Users,
  Brain,
  MessageSquarePlus,
  ShieldCheck,
  ScrollText,
  Menu,
  X,
  Radio,
} from "lucide-react";

const NAVIGATION_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agent Roster", icon: Users },
  { href: "/risk", label: "Risk Gates", icon: ShieldCheck },
];

const DESK_APPS = [
  { href: "/ask", label: "Desk Copilot", icon: MessageSquarePlus },
  { href: "/memory", label: "L3 Memory", icon: Brain },
  { href: "/journal", label: "Audit Journal", icon: ScrollText },
];

function NavGroup({
  items,
  onNavigate,
}: {
  items: typeof NAVIGATION_ITEMS;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1" aria-label="Navigation Group">
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`group relative flex items-center gap-3 rounded-xl px-3 py-2 text-[13px] font-medium transition-all duration-150 ${
              active
                ? "bg-cyan-500/10 text-cyan-400 font-semibold border border-cyan-400/35 shadow-[0_0_20px_rgba(0,229,255,0.08)]"
                : "text-text-secondary hover:bg-white/[0.03] hover:text-white border border-transparent"
            }`}
          >
            <Icon
              size={17}
              className={`transition-colors duration-150 ${
                active ? "text-cyan-400" : "text-text-muted group-hover:text-text-secondary"
              }`}
              aria-hidden
            />
            <span className="tracking-tight">{label}</span>
            {active && (
              <span className="absolute right-2.5 h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00e5ff]" />
            )}
          </Link>
        );
      })}
    </nav>
  );
}

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        className="fixed left-4 top-3.5 z-50 rounded-xl border border-white/10 bg-[#0c101d] p-2 text-text-secondary hover:text-white lg:hidden shadow-xl"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close menu" : "Open menu"}
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>

      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed left-0 top-0 z-40 flex h-full w-16 flex-col border-r border-white/5 bg-[#080b14]/95 backdrop-blur-2xl px-2.5 py-5 transition-transform duration-300 md:w-56 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand Header */}
        <Link
          href="/"
          className="flex items-center gap-3 px-2 mb-6 group"
          onClick={() => setOpen(false)}
        >
          <div className="relative rounded-xl overflow-hidden border border-cyan-500/30 p-0.5 bg-[#05070e] shadow-[0_0_15px_rgba(0,229,255,0.15)] group-hover:border-cyan-400 transition-colors">
            <Image
              src="/brand/logo.png"
              alt="STONKS Logo"
              width={32}
              height={32}
              className="rounded-lg object-contain"
              priority
            />
          </div>
          <div className="hidden md:flex flex-col">
            <span
              className="stonks-wordmark text-sm font-extrabold tracking-wider text-white group-hover:text-cyan-400 transition-colors"
              data-text="STONKS"
            >
              STONKS
            </span>
            <span className="text-[9px] font-mono tracking-tight text-text-muted">
              v1.0 · Autonomous Desk
            </span>
          </div>
        </Link>

        {/* Section 1: Navigation */}
        <div className="mb-5">
          <div className="hidden md:block px-2 mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-text-muted">
            Navigation
          </div>
          <NavGroup items={NAVIGATION_ITEMS} onNavigate={() => setOpen(false)} />
        </div>

        {/* Section 2: Desk Engine */}
        <div className="mb-auto">
          <div className="hidden md:block px-2 mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-text-muted">
            Desk Engine
          </div>
          <NavGroup items={DESK_APPS} onNavigate={() => setOpen(false)} />
        </div>

        {/* Footer Station Card */}
        <div className="mt-auto hidden md:block pt-4 border-t border-white/5">
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3 text-[11px]">
            <div className="flex items-center justify-between text-text-muted mb-1.5">
              <span className="flex items-center gap-1.5">
                <Radio size={12} className="text-cyan-400 animate-pulse" />
                <span className="text-white text-[11px] font-semibold">Alpaca Paper</span>
              </span>
              <span className="font-mono text-[9px] text-cyan-400 font-bold">ACTIVE</span>
            </div>
            <p className="text-[10.5px] text-text-muted leading-snug">
              12-gate deterministic execution kernel.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
