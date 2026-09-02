# UI — STONKS Design System & Pages

> Grounded in the actual `Assets/logo.png` palette (extracted programmatically): deep navy `#04091B` field, white low-poly head, six pure spectral accents (`#FF0000 #00FF00 #0000FF #00FFFF #FF00FF #FFFF00`), natural green `#78D848`. The logo's RGB-split glitch scatter is the brand's signature motion.

## 1. Identity rules

- **"STONKS"** is the identity everywhere: nav, `<title>` (`STONKS — autonomous AI options desk`), README H1, video titles, mascot speech.
- The full name — *Strategic Trading & Orchestration Network for Knowledge-driven Systems* — appears in exactly three places: README subtitle, app footer tagline, submission description.
- Logo (`Assets/logo.png` → `apps/web/public/brand/logo.png`) in the top bar (32px) and README hero (220px). Favicon derived from it.

## 2. Design tokens

### Palette (logo-derived)

```
── SURFACES (the navy field) ────────────────────
bg-page            #04091B   (logo background — the whole app lives on it)
bg-card            #0A0F26   (navy + 4% white)
bg-card-hover      #101632
border            #1C2444
border-strong      #2A3560

── TEXT ─────────────────────────────────────────
text-primary       #F8F8F8   (logo white)
text-secondary     #A8B0D0
text-muted         #5E6788

── SEMANTIC (reserved strictly for data) ────────
profit / buy       #00FF87   (logo green pushed toward mint for contrast on navy)
loss / sell        #FF4D5E   (logo red softened for dark bg)
warning / risk     #FFB020
info               #4DA3FF

── THE CAST ACCENTS (from the logo's spectral scatter) ──
Prime (white)      #F8F8F8
Senti (blue)       #4DA3FF   (logo #0000FF lifted for contrast)
Toro (green)       #00FF87   (logo #00FF00 lifted)
Ursa (red)         #FF4D5E   (logo #FF0000 softened)
Verdi (purple)     #C77DFF   (logo #FF00FF toward violet)
Sgt. Gate (amber)  #FFB020   (logo #FFFF00 warmed)
XQ (cyan)          #00E5FF   (logo #00FFFF kept)
Sage (orange)      #FF8A3D   (between logo red & yellow)

── CHART SERIES ────────────────────────────────
#4DA3FF #00FF87 #C77DFF #FFB020 #00E5FF #FF4D5E
```

**Rules:** monochrome-first — spectral color appears only for agent identity and data (P/L, verdicts, status). Pure logo hues are the mascot's ink (they sit inside white-outlined characters); UI surfaces use the lifted variants for WCAG contrast. Every color cue pairs with a non-color cue (↑/↓, icon, label). Never gray-on-saturated.

### Typography

- **Geist Sans** (UI/body) + **Geist Mono** (tickers, prices, greeks, order IDs, timestamps). Sentence in Sans, number in Mono. `font-variant-numeric: tabular-nums` on all numeric columns. No Inter.
- Scale: display (portfolio value) 48–60px · page title 24px · section 20px · card heading 16px/600 · body 14–16px · label 13px · mono data 13–14px.

### Radii, depth, spacing

- Radii: 6px controls, 10px cards, 12px modals — concentric (outer = inner + padding).
- Elevation: layered transparent shadows on navy (`0 1px 0 #FFFFFF0D, 0 8px 24px #00000066`); borders only for structure/state. No nested cards, no gradients (the logo's glitch is the only "effect" and it's earned), no glow.

### The signature — RGB-split glitch

The logo's red/green/blue channel-split, used in exactly two places so it stays special:
1. **STONKS wordmark** on the top bar: on hover and on every trade fill, channels split ±2px for 180ms (`@keyframes glitch` with `text-shadow: 2px 0 #FF0000, -2px 0 #00FFFF`) then snap back.
2. **Mascot celebration**: Stonks Prime's facets flash the spectral scatter once per win.
Everywhere else: quiet. *Spend your boldness in one place.*

## 3. Layout & pages

**Shell:** left sidebar (STONKS logo + nav: Overview, Agents, Memory, Ask, Risk, Journal), icon-rail at md, Vaul drawer below lg. **Top bar:** wordmark (glitchable) · account value + today's P/L (live, mono) · market pill (OPEN/CLOSED from Alpaca clock) · `PAPER · ACCT-XXXXXXXX` badge · ⌘K palette · notifications.

### `/` Overview — the golden path
1. **KPI strip (4):** Portfolio Value · Today's P&L · Total P&L · Risk Budget Used (sparkline each; number tickers animate via Motion Values).
2. **Equity curve** vs $100k baseline, entry/exit markers linked to decision cards (Tremor area chart, 8 cols).
3. **The Desk** — the live feed (4-col right rail): mascot avatar (colored) → status pill → one-line narrator copy → relative time → model/cost chip; collapsible reasoning blocks; debate verdict chips (`TORO 0.7 / URSA 0.3 → VERDI: NEUTRAL-BULL 0.62`); gate results (`12/12 PASS` or `REJECTED: EVENT_RISK`); auto-scroll pinned to latest with "N new events" pill.
4. **Positions table:** symbol badge, structure tag (CONDOR/CSP/SPREAD), qty, entry, mark, unrealized P&L (signed, colored + arrow), DTE countdown, exit-rule status.
5. **Prime docked** bottom-right of the feed (200px) with caption ("Reading 14 NVDA articles — 3 mention earnings").

### `/agents` — the cast
Card per agent: portrait (mascot, colored ring), role, status, current task, last output, cost; click → expanded timeline of that agent's actions (Langfuse pattern). "Replay this decision" on closed-trade cards.

### `/memory` — the K in STONKS
- **L3 lessons** front and center: the lesson sentence, the losing trade that spawned it, and (the payoff) *where it was later applied* ("blocked an NVDA condor on Sep 3 — the trade it would have been lost 1.2%").
- L1 snapshot browser + L2 ledger below.

### `/ask` — the copilot
Input + suggested chips ("invest in NVDA", "hedge the book", "why did we pass on SPY?"). Each request shows: the desk's queued analysis → live pipeline progress (Senti → debate → verdict → gates) → honest answer. Rejections are first-class results, styled as proudly as approvals.

### `/risk` — Sgt. Gate's wall
The 12 gates as live tiles (current config, last verdict, lifetime pass/reject counts), the exit ladder config, daily-halt status, and the restrict-only parameter history (every tightening Sage proposed, applied, with timestamps).

### `/journal`
Full append-only log — filters by agent/verdict/symbol. The "receipts" page for judges.

### Decision card (component, used everywhere)
Thesis (1–2 lines) · verdict chips with conviction · Senti's sentiment mini-bar with citations popover · Greeks snapshot (Δ Θ ν IV, mono) · gate grid (12 cells, green/red, reason code on hover) · order details (`client_order_id` mono) · post-mortem link if Sage visited it.

## 4. Motion spec (exact values)

| Interaction | Spec |
|---|---|
| High-frequency (table hover, feed ticks, pill updates) | instant or ≤150ms, opacity/color only |
| Enters | ease-out ≤300ms (`cubic-bezier(0.2, 0, 0, 1)`) |
| Exits | softer & shorter: `translateY(8px)` + fade |
| Button press | `scale(0.96)` |
| Icon swaps | opacity 0→1, scale 0.25→1, blur 4px→0 |
| Feed items | slide-in once, 200ms ease-out; `AnimatePresence initial={false}` |
| P/L numbers | Motion Values spring, no re-mount flash |
| Mascots | GSAP timelines per state (BRAND-AND-MASCOTS.md); `prefers-reduced-motion` → static pose + caption |
| Wordmark glitch | 180ms on hover/trade-fill only |

Static cue always accompanies motion (color/icon/label). No `transition: all`; exact properties only.

## 5. Responsive & quality floor

- Grid: 12 cols desktop / 6 tablet / 4 mobile; test at **375 / 768 / 1024 / 1440**.
- KPI strip 4-up → 2×2 → snap-scroll; charts full-width (min-height 280px); tables → stacked cards below md; feed → Vaul bottom sheet; `min-width: 0` on grid children; no horizontal scroll ever.
- Contrast ≥ 4.5:1 (lifted palette variants chosen for this); touch targets ≥ 44px; visible focus rings; keyboard nav for tables/drawers/palette; ARIA labels on icon-only buttons; feed updates in a polite live region.
- Performance: SSE single connection; reserved space for charts/feed (CLS < 0.1); Lighthouse ≥ 90 on Overview; lazy-load `/agents` portraits.

## 6. Copy rules (the desk's voice)

- Plain, confident, slightly memey but never unserious about risk. "Senti read 14 articles. Ursa wasn't convinced." / "Sgt. Gate said no. Here's why: EVENT_RISK — CPI in 18h."
- Numbers: mono, tabular, signed P/L (+$132.40 / −$48.10), one-decimal percents.
- Buttons: "Pause the desk", "Close position", "Export journal" — active voice, same name everywhere ("Pause the desk" → toast "Desk paused").
- Empty states invite action: "No open positions — the desk is scanning. Next cycle 10:35 ET."
- Errors direct, never apologetic: "Quote stream disconnected — retrying in 15s. Orders continue; marks may be stale."
