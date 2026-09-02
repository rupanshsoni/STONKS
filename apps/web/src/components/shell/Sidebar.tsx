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
} from "lucide-react";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Users },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/ask", label: "Ask", icon: MessageSquarePlus },
  { href: "/risk", label: "Risk", icon: ShieldCheck },
  { href: "/journal", label: "Journal", icon: ScrollText },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1" aria-label="Primary">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`flex items-center gap-3 rounded-radiu-control border-l-2 px-3 py-2 text-sm transition-colors ${
              active
                ? "border-l-prime bg-card text-text-primary"
                : "border-l-transparent text-text-secondary hover:bg-card-hover hover:text-text-primary"
            }`}
            style={{ borderRadius: 0 }}
          >
            <Icon size={18} aria-hidden />
            <span className="hidden md:inline">{label}</span>
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
        className="fixed left-4 top-4 z-50 rounded-control border border-border-soft bg-card p-2 lg:hidden"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close menu" : "Open menu"}
      >
        {open ? <X size={20} /> : <Menu size={20} />}
      </button>

      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={`fixed left-0 top-0 z-40 flex h-full w-16 flex-col gap-6 border-r border-border-soft bg-card px-2 py-6 transition-transform md:w-52 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Link href="/" className="flex items-center gap-2 px-1 md:px-2" onClick={() => setOpen(false)}>
          <Image src="/brand/logo.png" alt="STONKS" width={32} height={32} className="rounded" priority />
          <span className="stonks-wordmark hidden text-sm text-text-primary md:inline" data-text="STONKS">
            STONKS
          </span>
        </Link>
        <NavLinks onNavigate={() => setOpen(false)} />
        <p className="mt-auto hidden px-2 text-[10px] leading-tight text-text-muted md:block">
          Strategic Trading &amp; Orchestration Network for Knowledge-driven Systems
        </p>
      </aside>
    </>
  );
}
