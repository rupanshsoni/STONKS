export interface CastMember {
  id: string;
  name: string;
  role: string;
  ink: string;
  quip: string;
}

export const CAST: CastMember[] = [
  { id: "prime", name: "Stonks Prime", role: "Orchestrator & narrator", ink: "#F8F8F8", quip: "The desk is open." },
  { id: "senti", name: "Senti", role: "Sentiment analyst", ink: "#4DA3FF", quip: "Fourteen articles. Three mention earnings." },
  { id: "toro", name: "Toro", role: "Bull researcher", ink: "#00FF87", quip: "Momentum is a friend." },
  { id: "ursa", name: "Ursa", role: "Bear researcher", ink: "#FF4D5E", quip: "It's expensive to be this right." },
  { id: "verdi", name: "Verdi", role: "Judge", ink: "#C77DFF", quip: "Verdict." },
  { id: "gate", name: "Sgt. Gate", role: "Risk kernel", ink: "#FFB020", quip: "Twelve gates. Zero exceptions." },
  { id: "xq", name: "XQ", role: "Executor", ink: "#00E5FF", quip: "Filled." },
  { id: "sage", name: "Sage", role: "Post-mortem & learning", ink: "#FF8A3D", quip: "We lost. We learned." },
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
