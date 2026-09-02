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
| Working prototype others can use online | Vercel + Render URLs (DEPLOYMENT.md) |
| Video presentation (≤5 min MP4) | Script in §4 |
| Slide presentation (PDF) | Outline in §5 |
| Public GitHub repository | github.com/rupanshsoni/STONKS — commits across the whole window (GIT-HISTORY.md) |
| Cover image (PNG/JPG 16:9) | Logo on navy + cast lineup + "STONKS" wordmark |
| Social engagement (up to 5 links, X + LinkedIn, tag both) | §6 plan |

## 2. Submission form fields (draft)

- **Title:** STONKS
- **Short description:** An autonomous multi-agent options desk where AI agents analyze sentiment, debate, pass a deterministic risk kernel, and trade defined-risk options live on your Alpaca paper account — then learn from their own losses.
- **Tags:** Alpaca, MCP, Python, Next.js, Gemini, GPT-4o, Featherless, LangGraph-free custom orchestration, SQLite
- **Demo URL:** (Vercel link)
- **App platform:** Vercel (web) + Render (desk worker)
- **GitHub:** https://github.com/rupanshsoni/STONKS
- **Alpaca paper account ID:** *(from `/v2/account` — filled on submission day)*
- **Social links:** *(filled as posted — §6)*

## 3. The one-pager (AI logic, risk gates, Alpaca infrastructure)

**STONKS — Strategic Trading & Orchestration Network for Knowledge-driven Systems**

**AI logic.** A trading-firm-shaped pipeline runs unattended every 15–30 min while markets are open: deterministic analysts (trend, IV rank, dealer-gamma regime, liquidity, event risk) and a sentiment analyst (Gemini Flash) that scores public opinion from Alpaca's news with per-source credibility weighting and citations; a bull↔bear debate (2 rounds); a GPT-4o judge issuing verdict + conviction; a deterministic structurer that picks strikes, wings, DTE and size — *LLMs never compute greeks, credits, or sizes; code does, and the LLMs argue over code-computed facts.* After execution, a narrator turns journal entries into the live feed. When a position sours, a post-mortem agent (GPT-4o) assigns root cause and writes a boolean-checkable lesson into L3 memory, which is injected into every future debate — and may propose restrict-only parameter tightening, so the desk can only become more careful over time.

**Risk gates.** Twelve deterministic gates score every proposal (none short-circuit, so the journal records how badly rejected trades failed): sanity/freshness, regime (VIX/GEX), volatility-risk-premium edge, event blackout, defined-risk atomicity, liquidity, credit quality, position size ≤ 1% NAV, portfolio risk ≤ 5% NAV, concentration, duplicate/idempotency, and a −2% daily-loss flatten-and-halt. The exit ladder runs before entries: 50% profit target, 2× credit stop, 21-DTE time stop, event and regime-flip closes. Max loss per position is structural (atomic multi-leg), and property tests verify the invariants.

**Alpaca infrastructure.** All three surfaces: the **Trading API** (alpaca-py) for orders/positions/data and a trade_updates WebSocket feeding SSE to the UI; the **official Alpaca MCP server** (uvx subprocess, pinned, toolsets filtered to account/trading/assets/stock-data/options-data/news) as the agent tool surface; and the **Alpaca CLI** as an independent reconciliation source each cycle ("a REST client cannot quietly agree with itself") plus dry-run previews in tests. Every order uses deterministic client_order_ids (restart-safe, duplicate-proof). Verified conventions: negative limit prices as credit floors on multi-leg orders; conservative bid/ask marking. Free-feed caveats (EOD OI, invisible 0DTE) are documented on the risk page rather than hidden. Trades on a dedicated $100k paper account, ID: *(filled at submission)*.

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

- [ ] Fresh $100k account ID captured in UI + submission field
- [ ] Repo public, README final, screenshots in, secrets scanned, MIT LICENSE
- [ ] Demo URL smoke-tested logged-out; SSE live; journal flowing
- [ ] Video ≤5 min MP4 exported + uploaded; slides PDF exported
- [ ] One-pager pasted into submission
- [ ] 5 social links collected
- [ ] Submitted by 12:00 CEST (5-hour buffer); every link clicked from the public view
