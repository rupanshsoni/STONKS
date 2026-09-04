# VIDEO — 4:30 submission script (record this, cut to ≤5:00 MP4)

> Setup before recording: open **https://stonks-five-alpha.vercel.app** logged-out in a clean browser profile, 1440p, dark room, captions ON, kill notifications. Open these tabs in advance: Overview, /agents, /journal, /risk, /memory. Have https://stonks-cri1.onrender.com/health open in a background tab for the account-ID moment.

## Beat sheet (timestamps = target)

| Time | Say / Do | Screen |
|---|---|---|
| **0:00–0:15** | "Alpaca asked for autonomous AI trading agents. We staffed an entire trading desk." | Landing — logo, badges, market status |
| **0:15–0:35** | "Eight specialists. Deterministic analysts, a sentiment analyst with citations, a bull and bear that debate, a judge, a twelve-gate risk kernel, an executor, and a post-mortem agent that learns from losses." Scroll the roster slowly. | /agents — hover 3–4 mascots (Toro, Verdi, Sgt. Gate, Sage) |
| **0:35–1:05** | "The doctrine: LLMs argue, the math decides, Alpaca executes. Every strike, every greek, every size is code — the LLMs never touch a number that matters." Point at GLM 5.2 / MiniMax labels. | /agents + hover cards showing models |
| **1:05–1:50** | "This is a live cycle on our dedicated hundred-thousand-dollar paper account — ID PA3WFTQH47I4, shown right here." Open health JSON, point at account_id, back to Overview. "Watch the feed: Senti reads real news with citations… Toro and Ursa debate on code-computed facts… Verdi issues a verdict… and the twelve gates score it." Scroll Activity Log slowly. | Health JSON → Overview activity log |
| **1:50–2:30** | "Positions are marked live off option snapshots — no quote, we show a dash. Never a made-up number." Point at open positions table. "And here's the part we're proudest of: the desk says no. CPI in eighteen hours — Sgt. Gate rejected it, reason code journaled." Show a rejection event + open the gate grid. | Overview positions → /journal (filter rejections) → /risk |
| **2:30–3:10** | "Twelve deterministic gates, all scored, no short-circuit. Position cap one percent NAV, portfolio cap five, daily halt at minus two — flatten and stand down. Exits run before entries." Scroll the risk wall. | /risk — gate tiles with live pass/reject counts |
| **3:10–3:50** | "When we lose, Sage reviews the trade, writes a boolean-checkable lesson into memory, and can only propose *tightening* — the desk can get more careful, never more reckless." Show L3 lessons + param history. | /memory — lessons, param bounds |
| **3:50–4:15** | "All three Alpaca surfaces: Trading API is the executing path, MCP server as the agent tool surface, CLI for independent reconciliation every cycle. And the copilot: ask it to invest in NVDA, it faces the same pipeline and gates — no special treatment." Type an ask. | /ask — type "invest in NVDA", show queued |
| **4:15–4:30** | "LLMs argue. The math decides. Alpaca executes. STONKS — repo, demo, and live desk linked below." End card: logo + links. | Outro card |

## Recording rules
1. Golden path only — do not click into errors; if SSE reconnects, keep rolling (it's honest).
2. If the market is closed while recording, the "sleeping desk" is fine — narrate: "the desk sleeps between sessions; here's yesterday's cycle" and scroll the journal instead.
3. Re-record beats, not takes. Total silence gaps < 1s.
4. Export MP4 1440p, ≤5:00 hard, captions burned in.
5. Upload unlisted first, watch once end-to-end, check audio, then publish and paste the link into the submission.

## 30-second trailer cut (optional, for social)
0:00–0:05 cast lineup · 0:05–0:15 one live cycle timelapse (speed up journal) · 0:15–0:25 rejection + "we lost, we learned" Sage moment · 0:25–0:30 "STONKS" stinger.
