<div align="center">

<img src="Assets/logo.png" alt="STONKS" width="140" />

# STONKS

**Strategic Trading & Orchestration Network for Knowledge-driven Systems**

*An autonomous multi-agent AI options desk. LLMs argue; the math decides; Alpaca executes.*

[![Live Demo](https://img.shields.io/badge/LIVE_DEMO-stonks--five--alpha.vercel.app-00E5FF?style=for-the-badge&logo=vercel)](https://stonks-five-alpha.vercel.app)
[![Desk Worker](https://img.shields.io/badge/Desk_API-stonks--cri1.onrender.com-FF4D5E?style=for-the-badge&logo=render)](https://stonks-cri1.onrender.com/health)
[![Tests](https://img.shields.io/badge/tests-76%2F76-00FF87?style=for-the-badge&logo=pytest)](stonks/tests)
[![Paper Account](https://img.shields.io/badge/Alpaca_Paper-PA3WFTQH47I4-38BDF8?style=for-the-badge&logo=alpaca)](https://stonks-cri1.onrender.com/health)

**Built for the [Alpaca AI Trading Agents Hackathon](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon) — Options Alpha Agents track · Paper trading only**

[Demo](https://stonks-five-alpha.vercel.app) · [Desk API](https://stonks-cri1.onrender.com/health) · [Architecture](docs/ARCHITECTURE.md) · [Risk Kernel](docs/RISK.md) · [Agents](docs/AGENTS.md) · [Go-Live Runbook](docs/GO-LIVE.md)

</div>

---

## What it is

STONKS is a trading firm shrunk into a hackathon. Eight AI agents — a sentiment analyst, a bull/bear debate duo, a judge, a deterministic risk kernel, an executor, and a post-mortem analyst that learns from losses — run an **unattended cycle every 30 minutes while the market is open**, and narrate everything they do in a live web UI.

It trades **defined-risk options structures** (iron condors, credit spreads, wheel CSPs) on a dedicated Alpaca **paper** account, and it refuses to trade when the math says no — every rejection is journaled with reason codes and shown in the UI.

```
screener ─▶ analysts (code) ─▶ Senti (LLM, citations) ─▶ Toro ↔ Ursa (debate)
         ─▶ Verdi (judge) ─▶ structurer (code: strikes/wings/DTE/size)
         ─▶ Sgt. Gate: 12 deterministic gates ─▶ XQ: atomic multi-leg via Trading API
         ─▶ journal (JSONL + SSE) ─▶ web UI + mascots
                      └── Sage post-mortem ─▶ L3 lesson ─▶ injected into every future debate ─┘
```

**Live proof you can click right now:** the deployed desk at [stonks-five-alpha.vercel.app](https://stonks-five-alpha.vercel.app) is cycling against the live paper account `PA3WFTQH47I4` — check the Activity Log for real sentiment reports with news citations, debate verdicts, gate decisions (including honest rejections), and fills.

---

## The doctrine: LLMs argue, the math decides, Alpaca executes

Every number a judge might check — greeks, POP, credits, sizing, expected move, IV rank, VRP edge — is **code-computed** from live Alpaca market data with provenance. LLM outputs are schema-validated, and the only executable channel any LLM has is "select from the deterministic shortlist." No LLM ever computes a strike, a size, or a risk limit.

That separation is the whole security story:

| Layer | Who decides | Can it hallucinate a trade? |
|---|---|---|
| Research, sentiment, debate, verdict | LLMs (GLM 5.2 / MiniMax M3 via OpenRouter) | They can argue — never execute |
| Strikes, wings, DTE, size, greeks, POP | Pure code | No |
| 12-gate risk kernel | Pure code | No |
| Order routing, retries, reconciliation | Pure code | No |

---

## The cast

| Agent | Role | Engine |
|---|---|---|
| **Stonks Prime** | orchestrator & narrator | GLM 5.2 (narration only) |
| **Senti** | sentiment w/ citations + credibility weighting | GLM 5.2 |
| **Toro / Ursa** | bull & bear researchers | GLM 5.2 |
| **Verdi** | judge — verdict + conviction | MiniMax M3 |
| **Structurer** | deterministic menu (LLM confirms or passes — never invents) | MiniMax M3 |
| **Sgt. Gate** | 12-gate risk kernel | none — pure code |
| **XQ** | executor (API/MCP/CLI routing) | none — pure code |
| **Sage** | post-mortem & lessons | MiniMax M3 |

Every agent runs with failover: OpenRouter GLM → MiniMax → Gemini, and deterministic fallbacks if all LLMs are down — **the desk never dies because a provider did**. When a fallback answers, the journal says so (`model=fallback:rules`) — attribution is honest by construction.

---

## The risk kernel — 12 deterministic gates

Every proposal is scored against **all 12 gates** (no short-circuit — the journal records *how badly* a rejected trade failed):

```
 1 SANITY          quotes fresh (≤120s) & prices positive
 2 REGIME          VIX/GEX router allows the structure
 3 VRP_EDGE        implied-vs-realized vol edge ≥ threshold (per-symbol, live)
 4 EVENT_RISK      no entry inside macro blackout (CPI/FOMC/earnings calendar)
 5 DEFINED_RISK    atomic mleg — max loss structural
 6 LIQUIDITY       leg OI ≥ 250, spread ≤ 25% of mid
 7 CREDIT_QUALITY  credit ≥ 15% of width
 8 POSITION_SIZE   ≤ 1% NAV premium risk per structure
 9 PORTFOLIO_RISK  total open risk ≤ 5% NAV
10 CONCENTRATION   ≤ 2 structures per underlying
11 DUPLICATE       deterministic client_order_id (restart-safe)
12 DAILY_HALT      day P&L worse than −2% NAV → flatten & stand down
```

Exits run **before** entries (frees risk budget): 50% profit target, 2× credit hard stop, 21-DTE time stop, event and regime-flip closes.

## Self-improvement — the desk can only get more careful

Losing trades trigger **Sage's post-mortem**: root cause, failed signal, missed check, and a one-sentence boolean-checkable lesson written to **L3 memory** — injected into every future debate. Sage may also propose parameter tightenings, but a deterministic validator enforces **restrict-only bounds** (sizes and ceilings may only shrink; blackouts may only widen). Anything else is journaled as `REJECTED_PROPOSAL`. The desk cannot talk itself into more risk.

---

## Alpaca integration — all three surfaces

Built for the hackathon's requirements (Trading API mandatory; MCP server or CLI mandatory — we use both, API-first):

- **Trading API (alpaca-py-compatible REST)** — the primary executing surface. Orders, positions, account, clock, option chains + snapshots (OCC symbols, 100-symbol batching, OI from contracts, IV/greeks/volume hydrated), stock snapshots, screener endpoints, news, daily bars, portfolio history. WebSocket-safe SSE relays to the UI.
- **MCP server** — the official `alpaca-mcp-server` pinned subprocess, toolsets filtered to account/trading/assets/stock-data/options-data/news; used as the agent tool surface with documented, journaled degradation when unavailable on a host.
- **CLI** — independent position reconciliation each cycle ("a REST client cannot quietly agree with itself") plus `--dry-run` order previews in the gate pipeline. When the binary is absent (e.g. a PaaS host), reconciliation **abstains** rather than fabricate agreement — journaled, never silent.

Hard paper guard by construction: the client refuses any base URL that isn't `paper-api.alpaca.markets` and refuses `ALPACA_MODE != paper` — tested in CI.

---

## The web desk (Next.js 15, "Obsidian Blue" terminal)

Live at **[stonks-five-alpha.vercel.app](https://stonks-five-alpha.vercel.app)**:

- **Overview** — live equity curve (real points only), day/total P&L, open-risk vs portfolio-cap gauge, daily-halt gauge, gate decision stats, open positions with **live marks from option snapshots** (no quote → honest "marking…", never a fake number), real-time activity stream over SSE
- **Agents** — the full roster with live mascot states, active tasks, per-agent model labels straight from the route table
- **Risk wall** — the 12 gates with live pass/reject tallies, halt-line meter driven by the live config, exit-ladder rules
- **Journal** — the complete, filterable desk journal (every cycle, every verdict, every reason code)
- **Memory** — L1 snapshots, L2 ledgers, L3 lessons, restrict-only param history
- **Ask (copilot)** — type "invest in NVDA"; the request goes through the *same* pipeline — analysts, debate, all 12 gates — and the UI shows the honest verdict, including rejections

## Honesty guarantees (what we removed on purpose)

No fabricated data anywhere in the stack: equity curve renders live points only; positions show real snapshot mids or "—"; every journal event carries the model that actually answered; fixture candidates from test mode can never enter the live pipeline (the screener returns `[]` on failure, never fake symbols); CLI absent → abstain, not invent. Free-feed caveats (EOD OI, invisible 0DTE) are documented on the risk page rather than hidden.

---

## Quickstart

```bash
# desk worker (Python 3.11+)
pip install -r requirements.txt
cp .env.example .env           # add paper keys + OpenRouter keys
uvicorn stonks.api:app --reload

# web desk (Node 20+)
cd apps/web
echo 'NEXT_PUBLIC_DESK_URL=http://localhost:8000' > .env.local
pnpm install && pnpm dev       # http://localhost:3000
```

`STONKS_TEST=true` runs the entire pipeline deterministically — synthetic Black-Scholes chains, recorded LLM responses, dry-run orders — zero network, zero keys.

```bash
# 76 tests: gates, agents, alpaca surfaces, invariants
python -m pytest stonks/tests -q
```

Live smoke (no orders): `python scripts/probe_live.py` — validates account, clock, prices, screener, news, option chain, 16Δ legs, greeks, VIX proxy, VRP.

## Deployment (zero-cost)

- **Worker**: Render (blueprint via `render.yaml`) — https://stonks-cri1.onrender.com · `/health` gated on DB + Alpaca
- **Web**: Vercel (root `apps/web`, `NEXT_PUBLIC_DESK_URL` → Render) — https://stonks-five-alpha.vercel.app
- **Keep-awake**: UptimeRobot + GitHub Actions (`desk-health.yml`) during market hours; the broker is the source of truth across restarts (idempotent `client_order_id`s)

## Repo layout

```
stonks/            the desk worker (FastAPI orchestrator, agents, risk kernel, alpaca surfaces)
  ├─ orchestrator.py   the 30-min cycle: reconcile → exits → discover → debate → gate → execute
  ├─ agents/           LLM agents + failover bus (OpenRouter GLM/MiniMax, Gemini fallback)
  ├─ kernel/           12 gates, structuring, sizing, regime, exits — pure code
  ├─ alpaca/           client (API), mcp, cli, executor, reconcile — three surfaces
  ├─ api.py            /state /events(SSE) /ask /journal /memory /risk /health
  └─ tests/            76 tests, zero-network
apps/web/          the web desk (Next.js 15, TypeScript, Tailwind, SSE)
docs/              architecture, agents, risk, alpaca integration, submission pack
render.yaml        worker blueprint (free tier, health-checked)
```

## Docs

- [Architecture](docs/ARCHITECTURE.md) · [Agents & debate protocol](docs/AGENTS.md) · [Risk & restrict-only bounds](docs/RISK.md)
- [Alpaca integration](docs/ALPACA-INTEGRATION.md) · [Deployment](docs/DEPLOYMENT.md) · [Go-live runbook](docs/GO-LIVE.md)
- [Submission pack](docs/SUBMISSION.md) — one-pager, video script, checklist

---

<div align="center">

**LLMs argue. The math decides. Alpaca executes. STONKS.**

*Paper trading only. Not investment advice. Paper-trading results are hypothetical and do not represent actual trading.*

MIT License

</div>
