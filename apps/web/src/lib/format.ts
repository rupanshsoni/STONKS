export function fmtUSD(n: number, signed = false): string {
  if (!isFinite(n)) return "—";
  const abs = Math.abs(n);
  const str = abs.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const sign = n < 0 ? "−" : signed ? "+" : "";
  return `${sign}$${str}`;
}

export function fmtPct(n: number, signed = true): string {
  if (!isFinite(n)) return "—";
  const pct = n * 100;
  const abs = Math.abs(pct).toFixed(1);
  const sign = pct < 0 ? "−" : signed && pct > 0 ? "+" : "";
  return `${sign}${abs}%`;
}

export function signClass(n: number): string {
  if (n > 0) return "text-profit";
  if (n < 0) return "text-loss";
  return "text-text-secondary";
}

export function timeAgo(iso: string): string {
  const t = new Date(iso).getTime();
  if (isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 60) return `${Math.floor(s)}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function clockTime(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("en-US", { hour12: false });
}

export function structureTag(kind: string): string {
  const map: Record<string, string> = {
    iron_condor: "CONDOR",
    csp: "CSP",
    bull_put_spread: "BPS",
    bear_call_spread: "BCS",
  };
  return map[kind] ?? kind.toUpperCase();
}

export function agentInk(id: string): string {
  const map: Record<string, string> = {
    prime: "#F8F8F8",
    senti: "#4DA3FF",
    toro: "#00FF87",
    ursa: "#FF4D5E",
    verdi: "#C77DFF",
    gate: "#FFB020",
    xq: "#00E5FF",
    sage: "#FF8A3D",
    desk: "#A8B0D0",
  };
  return map[id] ?? "#A8B0D0";
}

export function agentName(id: string): string {
  const map: Record<string, string> = {
    prime: "Stonks Prime",
    senti: "Senti",
    toro: "Toro",
    ursa: "Ursa",
    verdi: "Verdi",
    gate: "Sgt. Gate",
    xq: "XQ",
    sage: "Sage",
    desk: "The Desk",
  };
  return map[id] ?? id;
}
