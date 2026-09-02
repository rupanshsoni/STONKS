# ALPACA INTEGRATION — API + MCP + CLI

> How STONKS uses all three Alpaca surfaces, as the problem statement intends: Trading API for the core loop, the **official MCP server** as the agent tool surface, and the **CLI** as an independent reconciliation/fallback path. Paper only.

## 1. Accounts & non-negotiables

- **Dedicated fresh paper account** created for this hackathon, starting balance **$100,000** — reused accounts are disqualified. The account ID (`account_number` from `GET /v2/account`) shows in the top bar badge, footer, and submission.
- **Options Level 3** enabled (multi-leg). Verified via `GET /v2/account/configurations` → `max_options_trading_level: 3`.
- Paper base: `https://paper-api.alpaca.markets` · data: `https://data.alpaca.markets`. **The client hard-asserts the paper URL and refuses live keys** (tested).

## 2. The three surfaces & their jobs

| Surface | Package/Transport | STONKS use |
|---|---|---|
| **Trading API** (REST + WS) | `alpaca-py` | Core loop: account, positions, portfolio history, orders, market data, option chains/snapshots (greeks/IV), screeners, news, calendar/clock; `wss://paper-api…/stream` for fills → SSE |
| **MCP server** (official) | `uvx alpaca-mcp-server` as stdio subprocess (pinned version) | The agent tool surface: the orchestrator's LLM tool-loop can call `get_option_chain`, `place_option_order`, `get_account_info`…; toolsets filtered to `account,trading,assets,stock-data,options-data,news` |
| **CLI** | `alpaca` binary via subprocess | (a) Independent position reconciliation each cycle — "a REST client cannot quietly agree with itself"; (b) scripted/cron fallback; (c) `--dry-run` order previews in tests |

Using all three (not just the required one) is the Technology-Implementation flex: each surface appears in the journal with a `surface` field, and the UI call-trace shows which surface did what.

## 3. Endpoint map (what we actually call)

**Trading:** `POST /v2/orders` (multi-leg `legs[]`), `GET /v2/orders`, `PATCH/DELETE /v2/orders/{id}`; `GET /v2/positions`, `DELETE /v2/positions/{symbol}`; `GET /v2/account`, `/v2/account/portfolio/history`, `/v2/account/activities`.
**Assets/options:** `GET /v2/assets`, `/v2/assets/{symbol}`; `GET /v2/options/contracts` (chain by underlying, expiration, strike), `/v2/options/contracts/{symbol_or_id}`.
**Market data:** stock bars/quotes/trades/snapshots + `/latest/*`; **option snapshots/chain** (greeks, IV); `/v1/screener/most-actives`, `/v1/screener/movers`; `/v1/news`; `/v1/corporate-actions`; `GET /v2/clock`, `GET /v2/calendar` (authoritative market hours — holidays/early closes).
**Streaming:** trade_updates WS (fills, partial fills) → SSE `order.filled` events → mascot celebrate + feed cards.

## 4. Options execution — verified conventions (from field research)

1. **Multi-leg credit sign:** credit spreads submit with a **negative `limit_price`** (e.g., `-1.21`); the limit acts as a **floor on credit received** (fills can improve it, e.g., -1.23). Debit spreads use positive limits.
2. **Atomic mleg only.** Every position is one multi-leg order — defined-risk is structural, naked legs impossible. Legs close atomically; if leg-closing is needed, short legs are closed first to avoid 403s.
3. **Conservative marking:** assume buy-at-ask / sell-at-bid; budget ~6.5% spread drag (measured by a competitor on a $520 credit).
4. **Idempotency:** deterministic `client_order_id` = `stonks-{intent}-{symbol}-{YYYYMMDDTHHMMSSZ}` — restart-safe, duplicate-proof (API rejects dupes).
5. **Free-feed caveats (documented honestly in the write-up):** the free `indicative` feed can omit OI/greeks on some endpoints; 0DTE contracts are invisible (~133k); OI timestamps are end-of-day. Mitigations: option snapshot/chain endpoints where greeks are present; liquidity gates use quote sizes when OI missing; GEX uses EOD OI with the caveat stated on the UI's risk page.

## 5. Integration patterns (code-level)

```python
# stonks/alpaca/client.py — paper guard
PAPER = "https://paper-api.alpaca.markets"
def guard():
    assert os.environ["ALPACA_MODE"] == "paper"
    assert _base_url() == PAPER        # refuses live keys/URLs

# stonks/alpaca/executor.py — surface routing
class Executor:
    def place(self, spec):                      # spec = gated structure
        coid = f"stonks-{spec.intent}-{spec.symbol}-{utc_stamp()}"
        for surface in ("mcp", "api"):         # CLI preview already ran in gate 11
            try: return self._place(surface, spec, coid)
            except SurfaceError as e: journal.surface_fail(surface, e)
        raise ExecutionHalt(spec, coid)

# stonks/alpaca/reconcile.py — every cycle, before anything else
def reconcile():
    rest = positions_map(api.get_positions())          # alpaca-py
    cli  = positions_map(cli.json("position", "list")) # subprocess, separate auth
    if rest != cli:
        journal.mismatch(rest, cli); halt_entries()     # never trade disputed state
    return rest
```

**MCP subprocess lifecycle:** pinned `alpaca-mcp-server` version in requirements.txt; supervisor starts it at boot, health-checks each cycle, restarts on failure; every MCP call is journaled with tool name + latency; timeout 90s per call, 300s per cycle. (A competitor got broken mid-hackathon by an unpinned fastmcp transitive bump — pinning is a documented lesson.)

**CLI usage:** installed in the worker image; every cycle runs `alpaca position list` + `alpaca account get` as the independent source of truth; `--dry-run` in the test suite validates order payloads without submitting; `--jq` filters keep parsing dependency-free.

## 6. Streaming → UI → mascots

```
Alpaca WS (trade_updates) ─┐
Desk cycle journal events ─┴─▶ SSE /events ─▶ browser zustand store
                                           ├─▶ KPI tickers (Motion Values)
                                           ├─▶ activity feed cards
                                           ├─▶ decision card updates
                                           └─▶ mascot state machine
```

One SSE connection per client; events are small, typed JSON; reconnect with backoff; the store renders from the journal (the journal is the audit trail, the SSE is just its live tail).

## 7. Rate limits & caching

- Free tier is limited — the desk uses snapshot endpoints, caches analyst data intraday (per-symbol, 15-min TTL), and never raw-polls quotes.
- MCP server docs warn about high-frequency querying: our cadence (15–30 min cycles) is far inside limits.
- WebSocket (fills) is push — no polling cost.

## 8. Secrets & safety

- Keys only in env (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_MODE=paper`); `.env` gitignored; repo secret-scanned pre-commit.
- The public API exposes read-only state + SSE; the only write endpoint is `/ask` (queues analysis, never orders).
- Live keys are structurally useless to the client: the guard refuses non-paper base URLs, and `ALPACA_MODE` must be `paper` — both covered by tests.

## 9. Test checklist

- [ ] Guard tests: live URL/key refusal (unit)
- [ ] Credit-sign tests: negative limit price payloads for credit structures (fixture)
- [ ] Idempotency: duplicate `client_order_id` rejected (mock)
- [ ] Reconciliation: injected REST/CLI mismatch → halt (unit)
- [ ] MCP supervisor: kill/restart round-trip (integration, mocked server)
- [ ] Dry-run: full order payload via CLI `--dry-run` (integration)
- [ ] Clock/calendar: market-open gating incl. early-close day (fixture)
