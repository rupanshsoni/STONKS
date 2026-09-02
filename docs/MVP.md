# MVP — Scope, Success Criteria & Build Order

> STONKS = Strategic Trading & Orchestration Network for Knowledge-driven Systems.
> This document defines what ships, what defers, and how we know it's done. Deadline pressure is real: **submissions close Fri Sep 4, 17:00 CEST**.

## 1. The one-sentence MVP

A live, deployed web app where judges can watch STONKS' agent cast analyze markets (sentiment + technicals + options flow), debate, pass a deterministic risk kernel, execute defined-risk options trades on a fresh $100k Alpaca paper account via API + MCP + CLI, and visibly learn from losing trades — narrated by meme-man mascots reacting in real time.

## 2. Must / should / could

### MUST (the submission is invalid or uncompetitive without these)
1. **Fresh dedicated $100k paper account** (created for this hackathon; ID visible in UI + submission) — reused accounts are disqualified.
2. **Options trading** in every strategy; Options Level 3 enabled; atomic multi-leg (defined-risk only).
3. **Alpaca MCP server AND CLI both integrated** (rules require at least one; we do both for max Technology Implementation score) alongside the Trading API.
4. **Autonomous loop**: desk scans → analyzes → debates → gates → executes → manages exits, unattended, all market-open hours.
5. **Sentiment analysis agent (Senti)**: public-opinion score per candidate from news/social-accessible sources + source-credibility weighting + expert-review synthesis, with citations.
6. **Two discovery paths**: autonomous trend-driven candidates (screeners) AND user-prompted ("invest in NVDA" via the Ask page → full pipeline on that ticker).
7. **Risk kernel**: 12 deterministic gates, journaled verdicts with reason codes, daily-loss halt.
8. **Self-improvement**: losing position (≤ −8% but above hard stop) triggers a post-mortem (why the prediction failed, which signal missed), lesson written to L3 memory, injected into future debates; restrict-only parameter tightening.
9. **Memory state**: L1 market snapshots / L2 position ledger / L3 lessons, persisted (SQLite), browsable in UI.
10. **Live web app**: deployed URL (Vercel + Render), showing equity curve, KPIs, agent activity feed with reasoning, positions, journal.
11. **Mascots**: Stonks Prime (logo character) + cast reacting to real events (idle/analyzing/reading-news/debating/trading/celebrating/post-mortem/risk-alert/sleeping).
12. **Submission pack**: public repo, ≤5-min video, PDF slides, one-page write-up (AI logic, risk gates, infrastructure), cover image, account ID, up to 5 social links.

### SHOULD (strong differentiators — protect if time tightens)
- Decision cards with full debate transcript + gate verdicts ("how badly did it fail")
- `/memory` page showing lessons learned + their effect on later trades
- Post-mortem cards in the feed (the "desk learns" demo moment)
- Equity curve with entry/exit markers tied to decision cards
- Alpaca call-trace transparency (which surface: API vs MCP vs CLI did what)
- REST-vs-CLI dual reconciliation status
- Mobile pass at 375px + reduced-motion
- 50+ tests, mainly on gates/kernel

### COULD (drop without pain, in this order)
- Rive polish for Stonks Prime (SVG+GSAP is the shipped baseline)
- Replay-a-decision on closed trades
- Greeks portfolio panel (net Δ/Γ/Θ/ν)
- Backtest stats page citing the strategy configs
- FastMCP cloud endpoint for judges to attach Claude/Cursor

## 3. Success criteria (measurable)

| Criterion | Target |
|---|---|
| Live paper trading | ≥ 6 completed trade cycles with journal entries by submission |
| Autonomy | Desk runs unattended ≥ 6 market hours without error halts |
| Gates | 12/12 gates implemented, each with tests; ≥ 1 journaled rejection exists |
| Self-improvement | ≥ 1 post-mortem completed with a lesson in L3 memory (or a simulated one demoed) |
| Sentiment | Every analyzed candidate carries a sentiment score + confidence + citations |
| UI | Lighthouse ≥ 90 perf on Overview; 30-second comprehension test (a stranger explains what the desk is doing) |
| Mascots | 8 characters, ≥ 5 states each, wired to real SSE events |
| Deadline | Submitted Fri Sep 4 by 12:00 CEST (5h buffer) |

## 4. Build order (dependency-driven)

**Phase 0 — unblock P&L clock (hour 0, blocking):** fresh $100k paper account, Options L3, keys in `.env`; repo init + first commit; docs pack.

**Phase 1 — trade (hours 0–3):** Alpaca client + paper guards; account/portfolio endpoints; clock/calendar; **first wheel CSP trade on SPY** (journal + SSE event even with rough UI). *Milestone: the account has activity.*

**Phase 2 — brain (hours 3–8):** analysts (code) → Senti (Gemini) → debate (Toro/Ursa) → judge (GPT-4o) → structurer (code menu) → 12 gates → executor (MCP + CLI) → exit ladder. *Milestone: one full pipeline cycle end-to-end, journaled.*

**Phase 3 — face (hours 6–12, parallel with 2):** Next.js shell + tokens; KPI strip + equity curve; activity feed (SSE) with collapsible reasoning; decision cards; positions table. *Milestone: Overview page tells the story live.*

**Phase 4 — memory & learning (hours 12–16):** L1/L2/L3 memory; Sage post-mortem agent + trigger; Ask page copilot; `/memory` page. *Milestone: desk visibly learns.*

**Phase 5 — cast & polish (hours 16–22):** 8 mascots wired to the event bus; states; glitch-RGB signature effect; mobile pass; reduced-motion; Sonner toasts on fills. *Milestone: the demo feels alive.*

**Phase 6 — ship (hours 22–26):** tests; deploy both surfaces + anti-sleep cron; README + screenshots; video; slides; one-pager; submission dry-run. *Milestone: submitted with buffer.*

**Triage rule if behind:** cut COULDs first, then SHOULD #7/#8. NEVER cut MUST 1–5 or 12. A trading, learning, journaling desk with a rough UI beats a beautiful shell that hasn't traded.

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Free-feed data gaps (0DTE invisible, EOD OI) | Use option snapshots/chain endpoints with greeks; document caveat honestly in write-up |
| Render free tier sleeps | Cron ping every 10 min (UptimeRobot/deploy hook); GitHub Actions fallback cycle |
| LLM cost/latency | Gemini Flash for cheap calls, cache analyst reports intraday, 2-round debate cap, ≤ 8 LLM calls/cycle |
| MCP version drift (fastmcp broke on a competitor mid-hackathon) | Pin `alpaca-mcp-server` version in requirements |
| One bad trade dominates the week | 0.5–1% NAV per structure, 2% daily halt — many small trades is the strategy |
| Mascot scope creep | SVG+GSAP baseline is the product; Rive is optional polish only |
| Judges' 1-week P&L is noise | Frame process metrics (trade count, win rate, expectancy, max DD) + honesty — it worked for past entries |

## 6. Out of scope (v2, post-hackathon)

Live trading (any real capital), crypto strategies, 0DTE engine, multi-user accounts/OAuth, backtest UI, mobile native app, Rive full-cast upgrade, multi-broker support.
