# STONKS — Strategic Trading & Orchestration Network for Knowledge-driven Systems

An autonomous multi-agent AI options desk that trades defined-risk structures on
a dedicated Alpaca **paper** account. LLMs argue; the math decides; Alpaca executes.

**Demo:** (deployed URL) · **Repo:** github.com/rupanshsoni/STONKS · **Alpaca paper account:** (ID)

![STONKS](Assets/logo.png)

## What it is

STONKS is a trading firm shrunk into a hackathon: eight AI agents — analysts, a
sentiment reader, a bull/bear debate, a judge, a deterministic risk kernel, an
executor, and a post-mortem analyst that learns from losses — run an unattended
cycle every 30 minutes while the market is open, and narrate everything they do
in a live web UI.

```
screener ─▶ analysts (code) ─▶ Senti (Gemini, citations) ─▶ Toro ↔ Ursa (debate)
        ─▶ Verdi (GPT-4o verdict) ─▶ structurer (code: strikes/wings/DTE/size)
        ─▶ Sgt. Gate: 12 deterministic gates ─▶ XQ: atomic multi-leg via MCP/API/CLI
        ─▶ journal (JSONL + SSE) ─▶ web UI + mascots
                     └────── Sage post-mortem ─▶ L3 lesson ─▶ injected into debates ─┘
```

- **Doctrine:** LLMs argue; the math decides; Alpaca executes. Greeks, POP,
  credits, and sizing are code-computed; LLM outputs are schema-validated, and
  the only executable channel an LLM has is "select from the deterministic
  shortlist."
- **Risk kernel:** 12 gates, all scored (no short-circuit), every verdict
  journaled with reason codes; exits run before entries; daily −2% flatten;
  1% NAV per structure, 5% portfolio cap.
- **Self-improvement:** losing trades trigger Sage's post-mortem; lessons go to
  L3 memory and are injected into every future debate; param proposals are
  **restrict-only** — the desk can only get more careful.
- **Alpaca:** all three surfaces — Trading API (REST), the official MCP server
  (pinned subprocess), and the CLI (independent position reconciliation each
  cycle).

## The cast

| Agent | Role | Model |
|---|---|---|
| Stonks Prime | orchestrator & narrator | Gemini Flash |
| Senti | sentiment w/ citations + credibility weighting | Gemini Flash |
| Toro / Ursa | bull & bear researchers | Gemini Flash |
| Verdi | judge | GPT-4o |
| Structurer | deterministic menu (LLM confirms only) | GPT-4o |
| Sgt. Gate | 12-gate risk kernel | none — pure code |
| XQ | executor (API/MCP/CLI routing) | none — pure code |
| Sage | post-mortem & lessons | GPT-4o |

## Quickstart

```bash
# desk worker (Python 3.11+)
pip install -r requirements.txt
cp .env.example .env       # add paper keys
uvicorn stonks.api:app --reload

# web app (Node 20+)
cd apps/web && pnpm install
echo 'NEXT_PUBLIC_DESK_URL=http://localhost:8000' > .env.local
pnpm dev
```

`STONKS_TEST=true` runs the entire pipeline with deterministic fixtures and
synthetic Black-Scholes chains — zero network, zero keys.

```bash
# tests (72 — gates, agents, alpaca surfaces)
python -m pytest stonks/tests -q
```

## Docs

- [MVP](docs/MVP.md) — scope & success criteria
- [Architecture](docs/ARCHITECTURE.md) — system design
- [Agents](docs/AGENTS.md) — roster, debate protocol, memory
- [Risk](docs/RISK.md) — the 12 gates, exit ladder, restrict-only bounds
- [Alpaca integration](docs/ALPACA-INTEGRATION.md) — API + MCP + CLI
- [UI](docs/UI.md) · [Brand & mascots](docs/BRAND-AND-MASCOTS.md)
- [Deployment](docs/DEPLOYMENT.md) · [Submission](docs/SUBMISSION.md) · [Git history](docs/GIT-HISTORY.md)

Built for the Alpaca AI Trading Agents Hackathon. Paper trading only.
