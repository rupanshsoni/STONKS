# ARCHITECTURE — System Design

> How STONKS is put together: components, data flow, and the reasoning behind every choice.

## 1. Bird's-eye view

```
                        ┌──────────────────────────┐
                        │   BROWSER (judges, you)  │
                        │  Next.js 15 · Vercel     │
                        └────────────┬─────────────┘
                                     │ HTTPS + SSE
                    ┌────────────────▼────────────────┐
                    │   DESK WORKER — FastAPI          │
                    │   Python 3.11 · Render (always   │
                    │   on during market hours)        │
                    │                                  │
                    │  /events  SSE stream             │
                    │  /state   snapshot (positions,   │
                    │           KPIs, agents, memory) │
                    │  /ask     copilot trigger        │
                    │  /journal /memory  introspection │
                    └───────┬──────────────┬───────────┘
                            │              │
              ┌─────────────▼───┐   ┌──────▼──────────────┐
              │  AGENT RUNTIME  │   │  ALPACA SURFACES     │
              │  (the desk)     │   │                      │
              │                 │   │  1. Trading API (REST │
              │  analysts       │   │     + WS) via alpaca- │
              │  debate/judge   │   │     py — orders,      │
              │  structurer     │   │     positions, data    │
              │  risk kernel    │   │  2. MCP server (uvx   │
              │  executor       │   │     alpaca-mcp-server)│
              │  post-mortem    │   │     — agent tool      │
              │  narrator       │   │     surface            │
              │                 │   │  3. CLI (subprocess) — │
              │  LLM routing:   │   │     independent       │
              │  Gemini Flash → │   │     reconciliation    │
              │    Senti/narr.  │   │     + fallback         │
              │  GPT-4o → judge │   └───────────────────────┘
              │  Featherless →  │
              │    1 analyst    │
              └───────┬─────────┘
                      │
        ┌─────────────▼───────────────┐
        │  STATE (SQLite + JSONL)       │
        │  · journal/decisions.jsonl   │
        │    (append-only, every verdict)│
        │  · memory: L1 snapshots,     │
        │    L2 position ledger,       │
        │    L3 lessons                │
        │  · config: gates, thresholds │
        └──────────────────────────────┘
```

## 2. Components

### 2.1 Web app (`apps/web` — Next.js 15, TypeScript, Vercel)
- App Router; server components for initial state fetch, client components for live views.
- **SSE consumption:** a single `EventSource` to the desk worker's `/events`; events fan out through a zustand store — one source of truth feeds KPIs, the feed, decision cards, AND mascots.
- Stack: Tailwind + shadcn/ui (Radix accessibility), Tremor (dashboard charts), TradingView lightweight-charts (price/candles), Motion (animation), Sonner (toasts), Vaul (mobile drawers), Lucide icons.
- Routes: `/` Overview · `/agents` cast + expanded timelines · `/memory` L3 lessons + L1/L2 · `/ask` copilot · `/risk` gates config + live verdicts · `/journal` full decision log.

### 2.2 Desk worker (`stonks/` — FastAPI, Render)
The always-on brain. A scheduler ticks the desk cycle **every 15–30 min while market is open** (Alpaca clock is the authoritative market-hours source — it knows holidays/early closes better than cron):

```
tick() when market open:
  1. reconcile()          # REST vs CLI positions; halt on mismatch
  2. manage_positions()   # exit ladder FIRST (frees risk budget)
  3. discover()           # screeners + /ask queue → candidates
  4. analyze()            # code analysts + Senti sentiment
  5. debate()             # Toro ↔ Ursa (2 rounds) → Verdi verdict
  6. structure()          # verdict+regime → menu; code picks strikes
  7. gate()               # 12 deterministic gates → APPROVE/REJECT
  8. execute()            # atomic mleg via MCP/CLI/API, idempotent
  9. journal()            # every step → JSONL + SSE event
  10. post_mortem_scan()  # losing positions → Sage triggers
after hours:
  sleep_cycle()           # reconcile + journal "desk sleeping"
```

### 2.3 Agent runtime (`stonks/agents/`)
- Each agent is a small class with a typed, schema-validated interface (Pydantic models in `stonks/schemas.py`). **Structured reports pass between agents; free-form language exists only inside debate rounds and narrator copy.**
- **Deterministic compute, LLM narration (the FinRobot doctrine):** greeks, POP, credit/width, expected move, sizing — all pure Python. LLMs receive code-computed facts and return only selections, verdicts, explanations.
- LLM routing (failover chain: configured primary → secondary → deterministic fallback so the desk never dies on a provider outage):
  - **Gemini Flash** — Senti (sentiment), news/event parsing, narrator (cheap, fast, structured output)
  - **GPT-4o** — Verdi (judge), Sage (post-mortem) (reasoning quality where it matters)
  - **Featherless AI** — one analyst role (hackathon partner tech — $25 credits; strengthens partner narrative)

### 2.4 Risk kernel (`stonks/kernel/`)
Pure functions + config. No LLM, no network. 12 gates, each independently testable, each returning `(pass: bool, reason_code, detail)`. See [RISK.md](RISK.md).

### 2.5 Alpaca integration (`stonks/alpaca/`) — see [ALPACA-INTEGRATION.md](ALPACA-INTEGRATION.md)
Three surfaces with distinct jobs:
1. **Trading API (alpaca-py)** — primary order path, account/positions/portfolio history, market data, WebSocket fills.
2. **MCP server (uvx alpaca-mcp-server, stdio subprocess)** — the agent tool surface: an LLM tool-loop can call `place_option_order`, `get_option_chain`, `get_account_info`… This satisfies the hackathon's MCP requirement *and* lets the judge-facing "attach Claude to STONKS" demo work.
3. **CLI (subprocess)** — independent second source of truth: position reconciliation ("a REST client cannot quietly agree with itself") + scripted/cron fallback path.

### 2.6 Memory (`stonks/memory/`) — the "Knowledge-driven" in the name
| Layer | Contents | Decay |
|---|---|---|
| L1 | Market snapshots per cycle (prices, VIX, IV rank, screener results) | 24h rolling |
| L2 | Open-position ledger (entry thesis, debate ref, exit rules, current P&L) | life of position |
| L3 | Distilled lessons from post-mortems ("don't open condors into CPI when IVR < 20") | near-permanent |

L3 lessons are injected into every debate prompt and the structurer's context — this is the self-improvement loop closing.

### 2.7 Journal (`stonks/journal/`)
Append-only JSONL — every cycle, every verdict, every rejection (with reason codes), every post-mortem, every fill. It is the audit trail the UI renders, the write-up cites, and the judges trust.

## 3. Key data flow — a trade's life

```
screener: SPY +3σ volume ──▶ candidate "SPY"
  code analysts: trend ✓ · IVR 31 ✓ · GEX + regime ✓ · liquidity ✓
  Senti: news 14 articles, social +0.22, expert reviews +0.41
        → sentiment 0.31 / conf 0.68 / citations [..]
  Toro: "momentum + sentiment + VRP rich → sell premium"
  Ursa: "event risk: CPI Thursday; gamma pins fragile"
  Verdi: NEUTRAL-BULLISH · conviction 0.62
  structurer (code): 16Δ iron condor · 38 DTE · wings $5 · credit $1.84
  Sgt. Gate: 12/12 PASS (reason codes journaled)
  XQ: mleg order via MCP · client_order_id stonks-ic-spy-20260903T1422Z
      → FILLED (credit $1.91) → SSE → mascot "trading" → feed card
  ...position drifts −8.4% one afternoon...
  Sage post-mortem: "entry ignored CPI proximity; lesson:
     block new premium-selling within 24h of CPI when IVR < 25"
     → L3 memory · future debates get the lesson injected
```

## 4. Technology choices — why

| Choice | Why |
|---|---|
| Next.js 15 + Vercel | App Router + SSE client support, zero-config deploys, judges get a fast URL; shadcn ecosystem |
| Python FastAPI worker | Official `alpaca-mcp-server` is Python/uvx; alpaca-py is first-class; agent loops need an always-on process, not serverless |
| SQLite | Zero-ops persistence on Render; the journal stays append-only JSONL for audit purity; both ship to git for transparency |
| Gemini + GPT-4o split | Cheap/fast for analysts (Gemini Flash), deep reasoning for judge/post-mortem (GPT-4o); Featherless for partner narrative |
| GSAP+SVG mascots | Full brand control, zero license risk, guaranteed ship; the meme-man aesthetic is literally low-poly facets — SVG polygons *are* the style |
| zustand | Tiny; the same event bus feeds UI, mascots, and toasts |
| Render free tier + cron ping | Hackathon-budget always-on; GitHub Actions as redundancy |

## 5. Failure modes & responses

| Failure | Response |
|---|---|
| LLM provider down | Failover chain (Gemini→GPT-4o→Featherless→deterministic fallback); journal notes which model answered |
| MCP server crash | Executor falls back to direct API orders; MCP supervisor restarts it; alert event |
| Render sleeps | Cron ping; on wake, reconcile against broker truth (broker is source of truth, never local state) |
| Alpaca rate limits | Snapshot endpoints + intraday analyst caching; no raw polling |
| Bad tick data | Sanity gate (quotes fresh, prices positive) rejects before any structure is built |
| Rest/CLI mismatch | Halt new entries; alert; reconcile — the desk never trades on disputed state |
| Duplicate order on restart | Deterministic `client_order_id`s (`stonks-{intent}-{sym}-{ts}`); API rejects dupes |

## 6. Security posture

- Paper-only guards: the client asserts `paper-api.alpaca.markets` and refuses live keys — tested.
- Keys only in env vars; `.env` gitignored; repo scanned (no secrets ever committed).
- The public API exposes read-only state + SSE; the only write endpoint is `/ask` (rate-limited, queue-only — it can request analysis, never directly order).
- Prompt-injection defense (Vetoed pattern): whitelisted news sources in analyst prompts; LLM outputs schema-validated; the LLM's only executable channel is "select from the deterministic shortlist."

## 7. Post-hackathon trajectory

The architecture deliberately separates the desk (strategy/agents) from the surfaces (API/MCP/CLI) so v2 can add backtests (replaying journal + L1 snapshots), a 0DTE engine, OAuth multi-user, or live-mode behind a hard opt-in wall.
