# SUBMISSION — Checklist, One-Pager, Video Script

> Everything required by the Alpaca AI Trading Agents Hackathon, assembled as we build so the final submission is a copy-paste exercise. **Deadline: Fri Sep 4, 17:00 CEST — target submit by 12:00.**

## 1. Requirements traceability (from the event page)

| Requirement | Where it's satisfied |
|---|---|
| Autonomous AI trading agents using Alpaca's Trading API | The desk worker's unattended cycle loop (ARCHITECTURE.md §2.2) |
| Uses Alpaca's MCP server **or** CLI | **Both**: official `alpaca-mcp-server` subprocess + CLI reconciliation (ALPACA-INTEGRATION.md §2) |
| All strategies incorporate options trading | Wheel CSPs, iron condors, credit spreads — options-only desk (AGENTS.md §6) |
| Developed/tested in paper trading environment | Fresh $100k dedicated paper account; hard paper guards |
| **Brand-new paper account for the submission** (reused = disqualified) | Created day 1; ID captured in UI badge + this submission |
| Starting balance $100,000 | Verified via `/v2/account` |
| **Alpaca paper trading account ID included** | Top-bar badge + submission field + one-pager |
| **One-page write-up: AI logic, risk gates, Alpaca infrastructure** | §3 below |
| Working prototype others can use online | https://stonks-five-alpha.vercel.app (Vercel) + https://stonks-cri1.onrender.com (Render) |
| Video presentation (≤5 min MP4) | Script in §4 |
| Slide presentation (PDF) | Outline in §5 |
| Public GitHub repository | github.com/rupanshsoni/STONKS — commits across the whole window (GIT-HISTORY.md) |
| Cover image (PNG/JPG 16:9) | Logo on navy + cast lineup + "STONKS" wordmark |
| Social engagement (up to 5 links, X + LinkedIn, tag both) | §6 plan |

## 2. Submission form fields (FINAL — copy-paste)

- **Title:** STONKS — Strategic Trading & Orchestration Network for Knowledge-driven Systems
- **Short description:** An autonomous multi-agent options desk where AI agents analyze sentiment, debate, pass a deterministic 12-gate risk kernel, and trade defined-risk options live on a dedicated Alpaca paper account — then learn from their own losses.
- **Demo URL:** https://stonks-five-alpha.vercel.app
- **App platform:** Vercel (web desk) + Render (desk worker)
- **Worker API:** https://stonks-cri1.onrender.com (health: /health)
- **GitHub:** https://github.com/rupanshsoni/STONKS
- **Alpaca paper account ID:** **PA3WFTQH47I4** (dedicated, $100k start — verified via /v2/account and /health)
- **Tags:** Alpaca, Trading API, MCP, CLI, Options, Multi-Agent, Python, FastAPI, Next.js, OpenRouter, GLM, MiniMax
- **Video:** (paste uploaded MP4 link)
- **Slides:** (paste PDF link)
- **Social links:** (paste up to 5 — X + LinkedIn, tagging @lablabai @AlpacaHQ)

### Long description (paste as-is)

STONKS is an autonomous multi-agent AI options desk for Alpaca's paper environment. Eight specialized agents run an unattended 30-minute cycle: deterministic code analysts (trend, IV rank, gamma-weighted dealer exposure, liquidity, event risk) and a sentiment analyst that reads real Alpaca news with per-source credibility weighting and citations; a bull/bear debate (Toro vs Ursa, 2 rounds, claims must cite analyst facts); a judge (Verdi) issuing direction + conviction; a deterministic structurer that picks every strike, wing, DTE, and size — LLMs never compute a tradeable number. Every proposal then faces Sgt. Gate: twelve deterministic gates (sanity, regime, VRP edge, event blackout, defined-risk atomicity, liquidity, credit quality, 1% NAV position cap, 5% portfolio cap, concentration, duplicate-idempotency, and a −2% daily flatten-and-halt) — all scored, none short-circuit, every verdict journaled with reason codes. The executor (XQ) places atomic multi-leg orders through Alpaca's Trading API with idempotent client_order_ids, with the official MCP server as the agent tool surface and the Alpaca CLI providing independent position reconciliation every cycle. When a position sours, Sage's post-mortem assigns root cause and writes a boolean-checkable lesson into L3 memory that is injected into every future debate — and its parameter proposals are restrict-only, so the desk can only become more careful over time. The whole desk narrates itself in a live web UI: real-time SSE feed, live equity curve and position marks from option snapshots, the complete filterable journal, and a copilot ("invest in NVDA") that faces the same analysts, debates, and gates — including honest rejections, shown with reasons. Doctrine: LLMs argue; the math decides; Alpaca executes.

## 3. The one-pager (AI logic, risk gates, Alpaca infrastructure)

**STONKS — Strategic Trading & Orchestration Network for Knowledge-driven Systems**

**AI logic.** A trading-firm-shaped pipeline runs unattended every 30 min while markets are open: deterministic analysts (trend, IV rank, gamma-weighted dealer exposure, liquidity, event risk) and a sentiment analyst (GLM 5.2 via OpenRouter) that scores public opinion from Alpaca's news with per-source credibility weighting and citations; a bull↔bear debate (2 rounds, claims must cite code-computed facts); a MiniMax M3 judge issuing verdict + conviction; a deterministic structurer that picks strikes, wings, DTE and size — *LLMs never compute greeks, credits, or sizes; code does, and the LLMs argue over code-computed facts.* After execution, a narrator turns journal entries into the live feed. When a position sours, a post-mortem agent (MiniMax M3) assigns root cause and writes a boolean-checkable lesson into L3 memory, which is injected into every future debate — and may propose restrict-only parameter tightening, so the desk can only become more careful over time. Cross-provider failover (GLM → MiniMax → Gemini, then deterministic rules) keeps the desk alive, with honest model attribution on every journal event.

**Risk gates.** Twelve deterministic gates score every proposal (none short-circuit, so the journal records how badly rejected trades failed): sanity/freshness, regime (VIX/GEX), volatility-risk-premium edge, event blackout, defined-risk atomicity, liquidity, credit quality, position size ≤ 1% NAV, portfolio risk ≤ 5% NAV, concentration, duplicate/idempotency, and a −2% daily-loss flatten-and-halt. The exit ladder runs before entries: 50% profit target, 2× credit stop, 21-DTE time stop, event and regime-flip closes. Max loss per position is structural (atomic multi-leg), and property tests verify the invariants.

**Alpaca infrastructure.** The **Trading API is the primary executing surface** (alpaca-py-compatible REST): orders/positions/account/clock, option chains + snapshots with OCC symbols and 100-symbol batching (OI from contracts; IV, greeks, volume hydrated live), stock snapshots, screener endpoints, news, daily bars, and portfolio history — all feeding a live SSE stream to the UI. The **official Alpaca MCP server** (pinned subprocess, toolsets filtered to account/trading/assets/market-data/options-data/news) serves as the agent tool surface. The **Alpaca CLI** provides independent position reconciliation every cycle and `--dry-run` order previews in the gate pipeline — when the binary is absent on a host, reconciliation abstains and journals it rather than fabricate agreement. Every order uses deterministic client_order_ids (restart-safe, duplicate-proof), and a hard guard refuses any non-paper base URL or mode (tested). Trades on a dedicated $100,000 paper account, ID: **PA3WFTQH47I4**.

## 4. Video script (4:00 target, ≤5:00 hard)

| Time | Beat | Screen |
|---|---|---|
| 0:00–0:20 | "Alpaca asked for autonomous AI trading agents. We staffed a whole desk." — STONKS title, logo glitch | Landing/top bar |
| 0:20–0:50 | The cast one-liner (each mascot flashes on its job) + architecture in 15s | /agents |
| 0:50–2:20 | **Live cycle**: screener finds a candidate → Senti reads news with citations → Toro/Ursa debate → Verdi verdict → Sgt. Gate 12/12 → XQ fills via MCP — journal proving each step | Overview feed + decision card |
| 2:20–3:00 | The honest moment: a rejection ("Sgt. Gate said no — CPI in 18h") and **Sage's post-mortem**: a loss → root cause → lesson lands in memory → *later blocked a similar trade* | /memory + /risk |
| 3:00–3:40 | Results: equity curve, trade table, process stats; all three Alpaca surfaces in the call-trace | Overview + journal |
| 3:40–4:00 | "LLMs argue. The math decides. Alpaca executes. STONKS." + team + repo/demo links | Outro card |

Recording notes: 1440p, follow the golden path only, captions on, no dead air; re-record beats, not the whole take.

## 5. Slides outline (PDF, 10 pages)

1. Title — STONKS logo, team, one-liner
2. The problem → our take (a *desk*, not a bot)
3. Architecture diagram (from README)
4. The cast (8 mascots + roles)
5. AI logic: analysts → sentiment w/ citations → debate → judge (structured, code-computed facts)
6. Risk kernel: 12 gates + exit ladder + invariants
7. Self-improvement: post-mortem → L3 memory → restrict-only adaptation
8. Alpaca: API + MCP + CLI — the three surfaces + account ID
9. Live results: equity curve, stats table, honest limitations
10. Demo screenshots + links + "what's next"

## 6. Social plan (Build in Public — 2 × $500 prizes)

Up to 5 links (X + LinkedIn, tagging @lablabai @AlpacaHQ). Cadence:
1. **Day 1 AM:** intro post — the cast lineup image + "we staffed an entire trading desk with meme-men" + architecture sketch
2. **Day 1 PM:** mascot teaser — GIF of Prime's glitch-celebration on a real fill
3. **Day 2 AM:** the honest-rejection post — "our desk said no to a condor 18h before CPI; here's the journal reason code" (differentiated content)
4. **Day 2 PM:** Sage post — "our agent reviewed its own losing trade, wrote itself a lesson, and blocked the same mistake later" + screenshot
5. **Submit day:** results + demo video + repo link

Engage bidirectionally (comment on other teams' builds) — engagement is two-way.

## 7. Final-day checklist

- [x] Fresh $100k account ID captured: **PA3WFTQH47I4** (UI badge + /health + this doc)
- [x] Deployed demo: https://stonks-five-alpha.vercel.app · worker https://stonks-cri1.onrender.com (verified logged-out, SSE live, CORS locked)
- [x] Repo public, README final (badges, links, honesty guarantees), secrets scanned, MIT LICENSE
- [x] One-pager final (§3, API-primary wording, real account ID)
- [ ] Video ≤5 min MP4 — script in **[VIDEO-SCRIPT.md](VIDEO-SCRIPT.md)** (beat sheet with timestamps)
- [ ] Slides PDF — 10-page outline in §5
- [ ] Cover image 16:9 (logo on navy + cast lineup)
- [ ] 5 social links collected (X + LinkedIn, tag @lablabai @AlpacaHQ)
- [ ] Submit on lablab before 17:00 CEST; every link clicked from a logged-out browser

> Recording the video: follow `docs/VIDEO-SCRIPT.md` — 4:30 beat sheet, golden-path only, re-record beats not takes, captions on, export 1440p MP4.
