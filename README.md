<div align="center">

<img src="Assets/logo.png" alt="STONKS logo" width="220" height="220" />

# STONKS

**Strategic Trading & Orchestration Network for Knowledge-driven Systems**

*An autonomous multi-agent AI options desk that runs live on Alpaca paper trading — where LLM agents debate, a deterministic risk kernel decides, and the desk learns from its own mistakes.*

[Live Demo](https://stonks.vercel.app) · [Architecture](docs/ARCHITECTURE.md) · [The Cast](docs/BRAND-AND-MASCOTS.md) · [Risk Kernel](docs/RISK.md)

</div>

---

## What is STONKS?

STONKS is an autonomous options-trading desk staffed by AI agents, built for the [Alpaca AI Trading Agents Hackathon](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon). It trades defined-risk options structures (the wheel, iron condors, credit spreads) on a dedicated **$100,000 Alpaca paper-trading account**, 24/5, with no human in the loop.

The desk mirrors how a real trading floor works:

```
        ┌───────────────── THE ANALYST DESK ─────────────────┐
        │  Senti (sentiment)   ·   code analysts (trend,    │
        │  options flow, volatility regime, event risk)     │
        └────────────────────────┬───────────────────────────┘
                                 ▼
        ┌───────────────── THE DEBATE ──────────────────────┐
        │   Toro (bull)  ↔  Ursa (bear)  →  Verdi (judge)    │
        └────────────────────────┬───────────────────────────┘
                                 ▼
        ┌───────────────── THE STRUCTURER ───────────────────┐
        │  verdict + regime → structure menu → code picks     │
        │  strikes, wings, size (the LLM never does the math) │
        └────────────────────────┬────────────────────────────┘
                                 ▼
        ┌───────────────── SGT. GATE (risk kernel) ───────────┐
        │  12 deterministic gates — every verdict journaled, │
        │  every rejection explained, naked risk impossible   │
        └────────────────────────┬────────────────────────────┘
                                 ▼
        ┌───────────────── XQ (executor) ────────────────────┐
        │  Alpaca Trading API + official MCP server + CLI     │
        │  atomic multi-leg orders, idempotent, reconciled     │
        └────────────────────────┬────────────────────────────┘
                                 ▼
        ┌───────────────── SAGE (self-improvement) ───────────┐
        │  losing trade? → post-mortem → lesson → L3 memory →  │
        │  injected into every future debate. The desk learns.  │
        └─────────────────────────────────────────────────────┘
```

**The rules of the desk:**

- **LLMs argue; the math decides; Alpaca executes.** Agents reason, select, and narrate. Every greek, probability, position size, and credit is computed by deterministic code.
- **Defined risk only.** Every position is an atomic multi-leg order with a structurally capped max loss.
- **The desk says no.** Every rejection is journaled with a reason code — a visible "no" is worth more than a hidden loss.
- **It learns in the open.** When a trade sours, Sage runs a post-mortem, writes the lesson to long-term memory, and the next debate starts smarter.

## The Cast

The desk is staffed by eight meme-man agents, each with a role, a color, and a personality — see them react live in the app:

| Agent | Role | Color |
|---|---|---|
| **Stonks Prime** | Orchestrator & narrator | White / spectrum glitch |
| **Senti** | Sentiment analyst (public opinion, sources, expert reviews) | Blue |
| **Toro** | Bull researcher | Green |
| **Ursa** | Bear researcher | Red |
| **Verdi** | Judge & verdict | Magenta/Purple |
| **Sgt. Gate** | Risk-kernel officer | Amber |
| **XQ** | Executor | Cyan |
| **Sage** | Post-mortem & self-improvement | Orange |

Full character spec: [docs/BRAND-AND-MASCOTS.md](docs/BRAND-AND-MASCOTS.md)

## Quickstart

```bash
# 1. Desk worker (Python 3.11+)
cp .env.example .env          # add ALPACA_API_KEY / ALPACA_SECRET_KEY (paper!) + LLM keys
pip install -r requirements.txt
uvicorn stonks.api:app --reload          # http://localhost:8000

# 2. Web app (Node 20+)
cd apps/web
pnpm install
pnpm dev                                 # http://localhost:3000
```

Detailed setup, env vars, and deployment: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Project layout

```
├── apps/web/               # Next.js 15 frontend (Vercel)
├── stonks/                 # Python desk worker (Render)
│   ├── agents/             #   analyst, debate, judge, structurer, post-mortem, narrator
│   ├── kernel/              #   12 risk gates + exit ladder
│   ├── alpaca/              #   API client + MCP + CLI (all three surfaces)
│   ├── memory/              #   L1/L2/L3 layered memory (SQLite)
│   ├── journal/             #   append-only decision log (JSONL)
│   └── api/                 #   FastAPI + SSE event stream
├── docs/                    # this documentation pack
└── Assets/                 # brand assets (logo.png)
```

## Documentation

| Doc | What's inside |
|---|---|
| [MVP.md](docs/MVP.md) | Scope, success criteria, build order |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, tech choices |
| [AGENTS.md](docs/AGENTS.md) | Agent roster, prompt schemas, debate protocol, sentiment spec, post-mortem & memory spec |
| [UI.md](docs/UI.md) | Design system (palette extracted from the logo), pages, motion spec |
| [BRAND-AND-MASCOTS.md](docs/BRAND-AND-MASCOTS.md) | Identity, the 8-character cast, states, animation technique |
| [ALPACA-INTEGRATION.md](docs/ALPACA-INTEGRATION.md) | Trading API + MCP server + CLI integration details |
| [RISK.md](docs/RISK.md) | The 12 gates, exit ladder, self-improvement thresholds |
| [GIT-HISTORY.md](docs/GIT-HISTORY.md) | Commit plan & annotated history |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Vercel + Render + env vars + cron |
| [SUBMISSION.md](docs/SUBMISSION.md) | Hackathon submission checklist, one-pager, video script |

## Disclaimer

STONKS trades on **paper only** (simulated funds, real market data). Educational/research project — not investment advice. Built for the Alpaca AI Trading Agents Hackathon; results are hypothetical.

## License

MIT
