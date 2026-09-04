# GO-LIVE RUNBOOK — from this repo to live paper trading

Order matters. Each step gates the next. Total time: ~60–90 min + a market session.

## 0. What was fixed (2026-09-03)

| Area | Fix |
|---|---|
| Executor | `order_class: "mleg"` (was invalid `"multi_leg"`); single-leg CSP sells use positive limits; closes use positive debit limits; string qty/prices; `position_intent` (open/close); order-poll uses `/v2/orders:by_client_order_id`; API-first routing |
| Data client | dedicated `data.alpaca.markets` httpx client; OCC symbols (not UUIDs); `snapshots` envelope unwrapping; OI from contracts endpoint, volume from `dailyBar.v`, IV from `impliedVolatility`; correct `v1beta1` stock endpoints |
| Regime/VIX | live VIX proxy from near-ATM SPY 28–40 DTE chain IV; live VRP edge = implied − 20-day realized (daily bars); IV rank computed from chain IV percentile — no more hardcoded 18.0/30.0 |
| LLMs | OpenRouter primary: GLM 5.2 free (senti/debate/narrator; auto-escalates to glm-5.3-flash on upstream 429) + MiniMax M3 free (judge/structurer/sage, JSON-mode verified); cross-provider fallbacks keep the desk alive; generous max_tokens for reasoning models |
| Structurer | budget-aware wing selection: wings tighten toward shorts until max-loss fits the 1% NAV POSITION_SIZE gate — the desk never proposes what its own gate must reject |
| CLI/reconcile | correct env vars (`ALPACA_API_KEY`/`ALPACA_SECRET_KEY`, `APCA_API_BASE_URL` dropped); reconcile ABSTAINS when the CLI is absent instead of fabricating a mismatch that would halt entries forever on Render |
| Health | honest `/health` (db+alpaca gate the status, MCP optional) + `account_id` exposed for the UI/submission badge |
| Events | calendar refreshed: FOMC 2026-09-16, CPI 2026-09-10, NVDA earnings 2026-09-23 |

## 1. Keys (5 min)

Fill `.env` (NEVER commit it). **OpenRouter keys are already set** (verified live
2026-09-03 — all 6 routes answered: GLM 5.2 free for Senti/Toro/Ursa/narrator,
MiniMax M3 free for Verdi/Structurer/Sage):

```
OPENROUTER_GLM_KEY=...        # DONE — z-ai/glm-5.2:free (auto-escalates to glm-5.3-flash on 429)
OPENROUTER_MINIMAX_KEY=...    # DONE — minimax/minimax-m3:free (JSON-mode verified)
ALPACA_MODE=paper
ALPACA_API_KEY=PK...          # paper dashboard → Generate API keys
ALPACA_SECRET_KEY=...
GEMINI_API_KEY=...            # OPTIONAL now (fallback surface)
OPENAI_API_KEY=...            # OPTIONAL now (fallback surface)
FEATHERLESS_API_KEY=...       # OPTIONAL
```

Note: GLM 5.2 free's upstream pool rate-limits hard at times — the client
auto-escalates to `z-ai/glm-5.3-flash` (same key, trivial cost) and falls
back to MiniMax/Gemini per route; the desk never dies on one provider.

## 2. Probe (2 min) — validates every live data path, zero orders

```
python scripts/probe_live.py
```

All `PASS` → continue. Any `FAIL` → that exact path is broken; do NOT enable trading.

## 3. One manual fill (10 min, market hours only: 13:30–20:00 UTC)

From a Python shell with keys loaded (verify with `python scripts/probe_live.py` first):

```python
import asyncio, os
from stonks.alpaca.client import AlpacaClient
from stonks.alpaca.executor import Executor
from stonks.schemas import Leg, StructureSpec

async def one_fill():
    c = AlpacaClient(test_mode=False)
    spy = (await c.snapshot_prices(["SPY"]))["SPY"]
    chain = await c.option_chain("SPY", 30, 45)
    puts = [e for e in chain if e.option_type == "put" and e.delta
            and -0.25 < e.delta < -0.10 and e.open_interest and e.open_interest > 250]
    short = max(puts, key=lambda e: abs(e.delta))          # ~0.16-0.20 delta put
    wings = [e for e in chain if e.option_type == "put" and e.strike < short.strike
             and short.strike - e.strike <= 3]
    wing = max(wings, key=lambda e: e.strike)               # nearest wide-enough wing
    credit = short.mid - wing.mid
    spec = StructureSpec(
        kind="bull_put_spread", intent="probe", symbol="SPY",
        legs=[Leg(option_symbol=short.option_symbol, side="sell", ratio=1,
                  strike=short.strike, option_type="put"),
              Leg(option_symbol=wing.option_symbol, side="buy", ratio=1,
                  strike=wing.strike, option_type="put")],
        expiry=short.expiry, dte=35, width=short.strike - wing.strike,
        credit=round(credit, 2), max_loss=round(short.strike - wing.strike - credit, 2),
        contracts=1, premium_risk=round((short.strike - wing.strike - credit) * 100, 2),
    )
    ex = Executor(test_mode=False)
    r = await ex.place(spec, "stonks-probe-SPY-manual-1")   # unique coid
    print(r.status, r.filled_avg_price, r.surface)
    r2 = await ex.close_position(spec)                      # buy it back
    print(r2.status, r2.surface)

asyncio.run(one_fill())
```

Expected: `filled` (or `accepted`→fills within seconds on paper), then a clean close. If the order is rejected, the 422 body is printed in the SurfaceError — send it to me.

## 4. Run the desk locally (one cycle)

```
# keep STONKS_TEST unset/false; market open only
python -m uvicorn stonks.api:app --host 127.0.0.1 --port 8000
# web UI in another terminal
cd apps/web; pnpm dev   # http://localhost:3000
```

Watch `/journal` (or the UI feed): expect `reconcile`, `senti_report`, `debate_verdict`,
`gate_verdict` (approvals AND honest rejections are both good), `order_filled`.
Kill switch: set `DESK_PAUSED=true` in `.env`, restart worker (exits still run).

## 5. Deploy (30 min)

**Render (worker):**
1. render.yaml is current. New Web Service → connect the repo → it reads render.yaml (`stonks-desk`, free).
2. Env vars (dashboard): the 5 keys + `CORS_ALLOW_ORIGIN=https://<your-vercel-domain>` (set after step 3 if unknown — editable later, triggers redeploy).
3. `/health` must return `"status": "ok"` with your account id.

**Vercel (web):**
1. Import repo → root directory `apps/web` (framework auto-detected).
2. Env var: `NEXT_PUBLIC_DESK_URL=https://<render-domain>.onrender.com`. Redeploy.
3. Open the site logged-out: state loads, SSE live badge connects (browser talks directly to Render).

**Keep-awake (Render free sleeps after 15 min idle):**
- UptimeRobot free monitor → ping `https://<render>/health` every 10 min, weekdays 13:30–20:00 UTC.
- GitHub Actions fallback exists (`.github/workflows/desk-health.yml`) — set repo secret `DESK_URL=https://<render-domain>.onrender.com`.

**Fresh start:** delete `data/` contents on the deployed instance before judging (Render disk starts empty — nothing to do; locally, clear `data/stonks.db*` + `data/journal/events.jsonl` if you want a clean journal).

## 6. Scoring-window ops (per DEPLOYMENT.md §5)

- Morning: `/health` green; journal shows overnight reconcile entries.
- Market open: cycles every 30 min; look for fills + at least one honest rejection in the journal (great demo material).
- If Render restarted: reconcile runs first; coids make duplicates impossible.
- Kill switch: `DESK_PAUSED=true` (entries stop, exits still run).

## 7. Submission-day (Fri Sep 4, submit by 12:00 CEST for the 17:00 deadline)

- [ ] Account ID: `python scripts/probe_live.py` prints it; also in `/health` and the UI top bar.
- [ ] README: fill Demo URL + repo links (placeholders on line 6).
- [ ] Video (≤5 min) — script in `docs/SUBMISSION.md` §4.
- [ ] One-pager — `docs/SUBMISSION.md` §3 (update the three-surfaces wording: API primary, MCP/CLI documented as degraded-optional surfaces).
- [ ] 5 social links; every link clicked from a logged-out browser.
