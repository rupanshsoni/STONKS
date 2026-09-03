export interface CastMember {
  id: string;
  name: string;
  role: string;
  model: string;
  ink: string;
  glow: string;
  quip: string;
  description: string;
}

export const CAST: CastMember[] = [
  {
    id: "prime",
    name: "Stonks Prime",
    role: "Orchestrator & Narrator",
    model: "Gemini 2.0 Flash",
    ink: "#FFFFFF",
    glow: "rgba(255, 255, 255, 0.25)",
    quip: "The desk is open. Math executes; conviction decides.",
    description: "Orchestrates 30-min market scan cycles, coordinates debates, and broadcasts narrative stream.",
  },
  {
    id: "senti",
    name: "Senti",
    role: "Sentiment & News Intelligence",
    model: "Gemini 2.0 Flash",
    ink: "#38BDF8",
    glow: "rgba(56, 189, 248, 0.25)",
    quip: "Fourteen articles parsed. Three mention earnings catalyst.",
    description: "Ingests real-time news, weighs credibility scores, and computes directional public lean.",
  },
  {
    id: "toro",
    name: "Toro",
    role: "Bull Researcher",
    model: "Gemini 2.0 Flash",
    ink: "#00FF87",
    glow: "rgba(0, 255, 135, 0.25)",
    quip: "Momentum is a friend. Greeks favor upside asymmetry.",
    description: "Constructs upside credit spreads, analyzes call delta, and argues bullish thesis.",
  },
  {
    id: "ursa",
    name: "Ursa",
    role: "Bear Researcher",
    model: "Gemini 2.0 Flash",
    ink: "#FF4D5E",
    glow: "rgba(255, 77, 94, 0.25)",
    quip: "It's expensive to be this right. Tail risks lurk in the wings.",
    description: "Stresses downside scenarios, event blackouts, and volatility expansion risks.",
  },
  {
    id: "verdi",
    name: "Verdi",
    role: "Presiding Judge",
    model: "GPT-4o",
    ink: "#C77DFF",
    glow: "rgba(199, 125, 255, 0.25)",
    quip: "Arguments heard. Final conviction recorded.",
    description: "Evaluates Toro vs Ursa debate rounds, assigns conviction scores, and issues final direction.",
  },
  {
    id: "gate",
    name: "Sgt. Gate",
    role: "12-Gate Risk Kernel",
    model: "Deterministic Kernel",
    ink: "#FBBF24",
    glow: "rgba(251, 191, 36, 0.25)",
    quip: "Twelve gates. Zero exceptions. No LLM overrules math.",
    description: "Evaluates 12 hard deterministic gates (VRP, liquidity, NAV caps, event blackout) before order staging.",
  },
  {
    id: "xq",
    name: "XQ",
    role: "Hypersonic Executor",
    model: "Alpaca API / MCP / CLI",
    ink: "#00E5FF",
    glow: "rgba(0, 229, 255, 0.25)",
    quip: "Order routed. Atomic multi-leg filled at mid.",
    description: "Executes atomic options structures across Alpaca REST, MCP subagent, and CLI reconciliation.",
  },
  {
    id: "sage",
    name: "Sage",
    role: "Post-Mortem & Memory",
    model: "GPT-4o",
    ink: "#FB923C",
    glow: "rgba(251, 146, 60, 0.25)",
    quip: "We lost. We learned. Tightening risk boundaries.",
    description: "Analyzes losing structures, extracts L3 lessons into memory, and submits restrict-only param tightenings.",
  },
];

export function castById(id: string): CastMember | undefined {
  return CAST.find((c) => c.id === id);
}

export function shade(hex: string, amount: number): string {
  const h = hex.replace("#", "");
  const n = parseInt(h, 16);
  let r = (n >> 16) & 255;
  let g = (n >> 8) & 255;
  let b = n & 255;
  if (amount >= 0) {
    r = Math.round(r + (255 - r) * amount);
    g = Math.round(g + (255 - g) * amount);
    b = Math.round(b + (255 - b) * amount);
  } else {
    r = Math.round(r * (1 + amount));
    g = Math.round(g * (1 + amount));
    b = Math.round(b * (1 + amount));
  }
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}
