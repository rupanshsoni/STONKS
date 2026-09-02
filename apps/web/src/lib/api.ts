import type { AskRequest, DeskState, JournalEvent } from "./types";

export const DESK_URL =
  process.env.NEXT_PUBLIC_DESK_URL || "http://localhost:8000";

export async function getState(): Promise<DeskState> {
  const res = await fetch(`${DESK_URL}/state`, { cache: "no-store" });
  if (!res.ok) throw new Error(`desk /state ${res.status}`);
  return res.json();
}

export async function ask(text: string): Promise<Partial<AskRequest>> {
  const res = await fetch(`${DESK_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`desk /ask ${res.status}`);
  return res.json();
}

export async function getJournal(limit = 500): Promise<JournalEvent[]> {
  try {
    const res = await fetch(`${DESK_URL}/journal?limit=${limit}`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export function streamEvents(
  onEvent: (e: JournalEvent) => void,
  onStatus: (connected: boolean) => void,
): () => void {
  let source: EventSource | null = null;
  let attempt = 0;
  let closed = false;
  const backoff = [1000, 2000, 5000, 10000];

  const connect = () => {
    if (closed) return;
    source = new EventSource(`${DESK_URL}/events`);
    source.addEventListener("hello", () => {
      attempt = 0;
      onStatus(true);
    });
    source.addEventListener("journal", (ev) => {
      try {
        onEvent(JSON.parse((ev as MessageEvent).data));
      } catch {
        /* skip malformed */
      }
    });
    source.addEventListener("ping", () => onStatus(true));
    source.onerror = () => {
      onStatus(false);
      source?.close();
      if (!closed) {
        setTimeout(connect, backoff[Math.min(attempt++, backoff.length - 1)]);
      }
    };
  };

  connect();
  return () => {
    closed = true;
    source?.close();
  };
}
