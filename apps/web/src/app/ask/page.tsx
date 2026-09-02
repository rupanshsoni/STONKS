"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/shell/Shell";
import { ask } from "@/lib/api";
import { useDeskStore } from "@/lib/store";
import { timeAgo } from "@/lib/format";
import { SendHorizonal } from "lucide-react";

const SUGGESTIONS = [
  "invest in NVDA",
  "hedge the book",
  "why did we pass on SPY?",
];

const STEPS = ["queued", "running", "answered"] as const;

function StatusStepper({ status }: { status: string }) {
  const rejected = status === "rejected";
  const activeIdx = rejected ? 2 : Math.max(STEPS.indexOf(status as "queued"), 0);
  return (
    <div className="flex items-center gap-1 text-[10px]">
      {STEPS.map((s, i) => {
        const done = i <= activeIdx && !rejected;
        const current = i === activeIdx;
        return (
          <span key={s} className="flex items-center gap-1">
            {i > 0 && <span className="text-text-muted">→</span>}
            <span
              className={`pill ${
                rejected && i === 2
                  ? "border-warning/50 bg-warning/10 text-warning"
                  : done
                    ? current
                      ? "border-info/50 bg-info/10 text-info"
                      : "border-profit/40 text-profit"
                    : "border-border-soft text-text-muted"
              }`}
            >
              {rejected && i === 2 ? "rejected" : s}
            </span>
          </span>
        );
      })}
    </div>
  );
}

export default function AskPage() {
  const state = useDeskStore((s) => s.state);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const asks = state?.ask_queue ?? [];

  useEffect(() => {
    const t = setInterval(() => setError(null), 6000);
    return () => clearInterval(t);
  }, [error]);

  const submit = async (value: string) => {
    const v = value.trim();
    if (!v || sending) return;
    setSending(true);
    setError(null);
    try {
      await ask(v);
      setText("");
    } catch {
      setError("The desk is unreachable — try again in a moment.");
    } finally {
      setSending(false);
    }
  };

  return (
    <Shell>
      <h1 className="mb-1 text-2xl font-bold">Ask the desk</h1>
      <p className="mb-4 max-w-2xl text-sm text-text-secondary">
        Requests enter the same pipeline as autonomous candidates: analysts,
        debate, and all twelve gates. The copilot can request analysis — it can
        never directly order. Rejections are results too.
      </p>

      <form
        className="card flex gap-2 p-3"
        onSubmit={(e) => {
          e.preventDefault();
          submit(text);
        }}
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="invest in NVDA"
          rows={2}
          className="min-w-0 flex-1 resize-none rounded-control border border-border-soft bg-page px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-info focus:outline-none"
          aria-label="Your request to the desk"
        />
        <button
          type="submit"
          disabled={sending || !text.trim()}
          className="flex h-10 items-center gap-2 rounded-control border border-info/40 bg-info/10 px-4 text-sm font-semibold text-info transition-transform active:scale-95 disabled:opacity-40"
        >
          <SendHorizonal size={16} aria-hidden />
          {sending ? "Sending…" : "Ask"}
        </button>
      </form>

      <div className="mt-2 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => submit(s)}
            className="pill border-border-soft text-text-secondary transition-colors hover:border-info/40 hover:text-info"
          >
            {s}
          </button>
        ))}
      </div>
      {error && <p className="mt-2 text-xs text-loss">{error}</p>}

      <section className="mt-6" aria-label="Requests">
        <h2 className="mb-2 text-base font-semibold">Requests</h2>
        {asks.length ? (
          <div className="space-y-3">
            {asks.map((a) => (
              <div
                key={a.id}
                className={`card p-4 ${a.status === "rejected" ? "border-warning/40" : ""}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold">{a.text}</p>
                  <StatusStepper status={a.status} />
                </div>
                {a.symbols.length > 0 && (
                  <p className="num mt-1 text-xs text-text-muted">
                    symbols: {a.symbols.join(", ")}
                  </p>
                )}
                {a.result_summary && (
                  <p
                    className={`mt-2 text-sm ${
                      a.status === "rejected" ? "text-warning" : "text-text-primary"
                    }`}
                  >
                    {a.result_summary}
                  </p>
                )}
                {a.status === "rejected" && (
                  <p className="mt-1 text-xs text-text-secondary">
                    The desk said no — and that&apos;s a result.
                  </p>
                )}
                <p className="num mt-2 text-[10px] text-text-muted">{timeAgo(a.created_ts)}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="card p-6 text-center text-sm text-text-secondary">
            No requests yet. Try one of the suggestions above.
          </div>
        )}
      </section>
    </Shell>
  );
}
