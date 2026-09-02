"use client";

import { useEffect, useRef, useState } from "react";
import { useDeskStore } from "@/lib/store";

interface Toast {
  id: number;
  text: string;
}

export default function Toaster() {
  const events = useDeskStore((s) => s.events);
  const seen = useRef<Set<string>>(new Set());
  const first = useRef(true);
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    if (first.current) {
      events.slice(0, 3).forEach((e) => seen.current.add(e.id));
      first.current = false;
    }
    const fresh = events.filter(
      (e) => e.type === "order_filled" && !seen.current.has(e.id),
    );
    fresh.forEach((e) => seen.current.add(e.id));
    if (fresh.length) {
      setToasts((t) => [
        ...fresh.map((e, i) => ({
          id: Date.now() + i,
          text: e.summary,
        })),
        ...t,
      ].slice(0, 4));
    }
  }, [events]);

  useEffect(() => {
    if (!toasts.length) return;
    const timer = setTimeout(() => setToasts((t) => t.slice(0, -1)), 5000);
    return () => clearTimeout(timer);
  }, [toasts]);

  if (!toasts.length) return null;

  return (
    <div
      className="fixed bottom-4 left-4 z-50 flex flex-col gap-2"
      role="status"
      aria-live="polite"
    >
      {toasts.map((t) => (
        <div key={t.id} className="card fade-enter flex items-center gap-2 px-4 py-3">
          <span className="text-profit text-sm font-bold">▲</span>
          <span className="text-sm">{t.text}</span>
        </div>
      ))}
    </div>
  );
}
