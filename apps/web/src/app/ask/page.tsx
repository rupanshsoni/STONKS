"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/shell/Shell";
import { ask } from "@/lib/api";
import { useDeskStore } from "@/lib/store";
import { timeAgo } from "@/lib/format";
import { SendHorizonal, Terminal, Sparkles, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";

const SUGGESTIONS = [
  "invest in NVDA",
  "hedge the book",
  "why did we pass on SPY?",
  "scan options chain for TSLA",
];

const STEPS = ["queued", "running", "answered"] as const;

function StatusStepper({ status }: { status: string }) {
  const rejected = status === "rejected";
  const activeIdx = rejected ? 2 : Math.max(STEPS.indexOf(status as "queued"), 0);

  return (
    <div className="flex items-center gap-1.5 text-[10px] font-mono">
      {STEPS.map((s, i) => {
        const done = i <= activeIdx && !rejected;
        const current = i === activeIdx;
        return (
          <span key={s} className="flex items-center gap-1.5">
            {i > 0 && <span className="text-text-muted">→</span>}
            <span
              className={`pill text-[9px] uppercase tracking-wider font-bold ${
                rejected && i === 2
                  ? "pill-loss"
                  : done
                  ? current
                    ? "pill-info animate-pulse"
                    : "pill-profit"
                  : "border-white/10 bg-white/5 text-text-muted"
              }`}
            >
              {rejected && i === 2 ? "Rejected by Gate" : s}
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
      setError("The desk is currently executing a 30m cycle or unreachable — please retry in a moment.");
    } finally {
      setSending(false);
    }
  };

  return (
    <Shell>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          Desk Copilot Command
          <span className="pill text-[10px] border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
            Interactive
          </span>
        </h1>
        <p className="text-xs md:text-sm text-text-secondary mt-1 max-w-2xl">
          Direct questions or candidate structures to the trading desk. All user prompts enter the exact same pipeline: Senti sentiment, Toro vs Ursa debate, Verdi verdict, and 12 deterministic gates.
        </p>
      </div>

      {/* Terminal Input Card */}
      <div className="card p-5 border-cyan-500/20 shadow-[0_0_25px_rgba(0,229,255,0.05)]">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-400 mb-3">
          <Terminal size={14} />
          <span>Autonomous Pipeline Prompt</span>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(text);
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. invest in NVDA credit spreads or analyze SPY..."
              rows={2}
              className="w-full resize-none rounded-xl border border-white/10 bg-[#060810] p-3 text-sm text-white placeholder:text-text-muted focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 font-mono"
              aria-label="Your request to the desk"
            />
          </div>
          <button
            type="submit"
            disabled={sending || !text.trim()}
            className="flex items-center justify-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-500/15 px-6 py-3 text-sm font-semibold text-cyan-400 transition-all hover:bg-cyan-500/25 active:scale-95 disabled:opacity-40 shrink-0"
          >
            <SendHorizonal size={16} />
            <span>{sending ? "Queuing..." : "Submit Proposal"}</span>
          </button>
        </form>

        {/* Suggestion Chips */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-[11px] text-text-muted font-medium">Quick Scenarios:</span>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => submit(s)}
              className="pill text-xs border-white/10 hover:border-cyan-500/40 hover:text-cyan-400 hover:bg-cyan-500/5 transition-colors cursor-pointer"
            >
              <Sparkles size={11} className="text-cyan-400" />
              {s}
            </button>
          ))}
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 text-xs text-red-400">
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Requests History */}
      <section className="mt-8" aria-label="Requests queue">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
            Candidate Pipeline History
          </h2>
          <span className="num text-xs text-text-muted">{asks.length} requests logged</span>
        </div>

        {asks.length ? (
          <div className="space-y-3">
            {asks.map((a) => {
              const isRejected = a.status === "rejected";
              return (
                <div
                  key={a.id}
                  className={`card p-5 transition-all ${
                    isRejected ? "border-red-500/30" : "border-white/5"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-white">
                        &ldquo;{a.text}&rdquo;
                      </span>
                      {a.symbols.length > 0 && (
                        <span className="pill font-mono text-[10px] border-cyan-500/30 bg-cyan-500/10 text-cyan-400">
                          {a.symbols.join(", ")}
                        </span>
                      )}
                    </div>

                    <StatusStepper status={a.status} />
                  </div>

                  {a.result_summary && (
                    <div className="mt-3 rounded-lg border border-white/5 bg-[#060811] p-3 text-xs">
                      <p
                        className={`font-medium leading-relaxed ${
                          isRejected ? "text-amber-400" : "text-text-primary"
                        }`}
                      >
                        {a.result_summary}
                      </p>
                      {isRejected && (
                        <p className="mt-1 text-[11px] text-text-muted">
                          Sgt. Gate enforced mathematical risk boundary — rejection recorded as a validated outcome.
                        </p>
                      )}
                    </div>
                  )}

                  <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-text-muted font-mono">
                    <span>ID: {a.id}</span>
                    <span>{timeAgo(a.created_ts)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center text-xs text-text-secondary">
            No pipeline requests in the current session. Click one of the quick scenarios above to test the autonomous cycle.
          </div>
        )}
      </section>
    </Shell>
  );
}
