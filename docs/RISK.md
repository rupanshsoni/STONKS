# RISK — The Kernel, Exit Ladder & Self-Improvement Config

> STONKS' safety is deterministic code, not LLM judgment. Every number here is a config constant (see §5), journaled, and testable. "LLMs argue; the math decides."

## 1. The 12 gates (Sgt. Gate)

All proposals are scored against **all 12** (no short-circuit) so the journal records *how badly* a rejected trade failed. Each verdict: `(pass: bool, reason_code, detail)`.

| # | Gate | Rule | Reason codes |
|---|---|---|---|
| 1 | `SANITY` | quotes fresh (≤ 2 min), prices positive, chain non-empty | `STALE_DATA`, `BAD_PRICE` |
| 2 | `REGIME` | structure allowed by regime router (VIX band + GEX sign) | `REGIME_STRESSED`, `GEX_NEGATIVE` |
| 3 | `VRP_EDGE` | implied-vs-realized edge ≥ threshold on the pricing model | `NO_EDGE`, `EDGE_BELOW_MIN` |
| 4 | `EVENT_RISK` | no entry inside blackout window for symbol/index events | `EVENT_BLACKOUT` |
| 5 | `DEFINED_RISK` | atomic multi-leg, max loss = width − credit, structurally capped | `NOT_ATOMIC`, `UNCAPPED` |
| 6 | `LIQUIDITY` | every leg OI ≥ 250, bid/ask ≤ 25% of mid | `LOW_OI`, `WIDE_SPREAD` |
| 7 | `CREDIT_QUALITY` | credit ≥ 15% of wing width | `THIN_CREDIT` |
| 8 | `POSITION_SIZE` | premium risked ≤ 1.0% NAV | `SIZE_EXCEEDED` |
| 9 | `PORTFOLIO_RISK` | total open risk ≤ 5% NAV | `BUDGET_EXCEEDED` |
| 10 | `CONCENTRATION` | ≤ 2 structures per underlying | `CONCENTRATION` |
| 11 | `DUPLICATE` | deterministic `client_order_id`; CLI `--dry-run` preview passes | `DUPLICATE_ORDER`, `PREVIEW_FAIL` |
| 12 | `DAILY_HALT` | day P&L > −2.0% NAV → flatten all, stand down till next session | `DAILY_HALT_TRIPPED` |

**Kernel invariants (property-tested):** for any structure the kernel approves, max loss per position ≤ 1% NAV and total ≤ 5% NAV *by construction*; a day cannot lose more than ~2% NAV + slippage on entries; naked short exposure is impossible (gate 5 is structural).

## 2. Exit ladder (management loop, runs before entries)

| Rule | Spec (per structure family) |
|---|---|
| Profit target | 50% of max credit received (condors/spreads) |
| Hard stop | 2× credit received (defined-risk max loss never reached) |
| Time stop | close at 21 DTE (gamma risk) — wheel rolls at 21 DTE instead |
| Event rule | close before symbol earnings; index-event blackout for entries |
| Regime flip | close structures whose entry regime inverts (e.g., GEX sign flip) |
| Market close safety | no position held into expiration weekend (defined by calendar) |

Every exit emits a journal entry (which rule fired, P&L attribution) → decision card closes out → mascot reacts (`celebrating` on target, `post_mortem` handoff if a loss).

## 3. Self-improvement thresholds (Sage)

| Constant | Default | Bounds (restrict-only) | Notes |
|---|---|---|---|
| `post_mortem_trigger_pct` | −8% unrealized (of premium risked) | −5% .. −12% | "down by a threshold, but above the hard stop" — triggers analysis, not exit |
| `post_mortem_trigger_closed` | loss ≥ 50% of max risk on close | 30% .. 80% | post-close review |
| `event_blackout_hours` | 24 | 12 .. 48 | may only increase (tighten) |
| `min_iv_rank` | 20 | 10 .. 35 | premium-selling floor |
| `max_position_size_pct` | 1.0% | 0.25% .. 1.0% | may only decrease |
| `daily_halt_pct` | 2.0% | 1.0% .. 2.5% | may only decrease |
| `vix_entry_ceiling` | 35 | 20 .. 35 | may only decrease |

**Restrict-only enforcement (code, not prompts):** Sage's `param_proposal` is validated against this table — any proposal that would *loosen* a limit, move outside bounds, or introduce a new parameter is journaled as `REJECTED_PROPOSAL` and never applied. Applied proposals are logged in `config_history` with before/after, timestamp, and the losing trade that motivated them — rendered on `/risk` as the "the desk got more careful" timeline. The asymmetry (the desk can only become more conservative from experience) is a core trust story.

## 4. Position sizing math (code-only)

```
risk_per_structure = min(max_position_size_pct × NAV, credit_floor × contracts)
contracts = floor(risk_budget / (width × 100 − credit × 100))
wheel CSP: notional ≤ 5% NAV per cycle, reserved cash tracked in L2
```

All arithmetic in `stonks/kernel/sizing.py`; LLMs never see the formula, only its outputs.

## 5. Config file (`stonks/config/risk.py` — constants, not secrets)

Single source of truth imported by kernel, executor, and the `/risk` UI. Changes enter via Sage's reviewed proposals only (or manual hotfix, journaled as `OPERATOR_OVERRIDE` — expected to remain unused during the competition).

## 6. Honest-limitations register (write-up material)

- Free-feed OI is EOD → intraday GEX is approximate (stated on `/risk`).
- 0DTE invisible in free data → 0DTE engine out of scope.
- ~1-week live window is statistical noise → we report process metrics (trade count, win rate, expectancy, max DD, gate rejection stats) alongside P&L.
- Bid/ask marking is conservative (buy ask/sell bid) → reported P&L slightly understates mid-mark.
