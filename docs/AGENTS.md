# AGENTS — Roster, Prompts, Debate, Sentiment, Post-mortem & Memory

> The complete behavioral spec of the STONKS cast: who does what, what they're allowed to touch, exact prompt schemas, and the self-improvement loop.

## 1. Roster & permissions model

| Agent | Kind | LLM | May decide | May NEVER |
|---|---|---|---|---|
| **Stonks Prime** | Orchestrator/narrator | Gemini Flash (narration only) | cycle timing, narration copy | trade, override gates |
| **Senti** | Sentiment analyst | Gemini Flash | sentiment score, confidence, citations | anything numeric about options |
| **Toro** | Bull researcher | Gemini Flash | debate arguments | new facts (must cite analyst reports) |
| **Ursa** | Bear researcher | Gemini Flash | debate arguments | new facts (must cite analyst reports) |
| **Verdi** | Judge | GPT-4o | verdict + conviction | strikes, sizing, bypassing gates |
| **Structurer** | Deterministic + LLM confirm | GPT-4o (confirm/pass only) | structure selection from menu | invent structures, compute greeks |
| **Sgt. Gate** | Risk kernel | **none — pure code** | APPROVE/REJECT + reason codes | be persuaded |
| **XQ** | Executor | **none — pure code** | order routing (API/MCP/CLI), retries | alter order terms post-gate |
| **Sage** | Post-mortem | GPT-4o | root cause, lesson draft, param-tightening proposal | loosen anything, originate trades |
| **Code analysts** | Deterministic | none | trend/IVR/GEX/liquidity/event-risk facts | LLM anything |

**Doctrine:** *LLMs argue; the math decides; Alpaca executes.* Every number a judge might check (greeks, POP, credit, sizing, expected move) is code-computed with provenance. LLM outputs are schema-validated; the only executable channel an LLM has is "select from the deterministic shortlist."

## 2. The cycle (tick every 15–30 min, market open only)

```
reconcile → manage_exits → discover → analyze → debate →
structure → gate → execute → journal → post_mortem_scan → narrate
```

Exits run **before** entries (frees risk budget). Every step emits a journal entry + SSE event with a timestamp, so the UI's activity feed is a literal rendering of the desk's brain.

## 3. Discovery — two paths (per requirements)

**Path A — Autonomous (trend-driven, "it can come up on its own"):**
1. Alpaca screener endpoints (most-actives, movers) + watchlist universe (SPY, QQQ, IWM, AAPL, MSFT, NVDA, TSLA).
2. Filters: optionable, leg liquidity (OI ≥ 250, spread ≤ 25% of mid), price range, not within event-blackout.
3. Ranked by |momentum| × novelty (unusual moves the desk hasn't seen today) → top 3 candidates enter analysis.

**Path B — Copilot (user-prompted, "prompt the LLM to invest in a stock"):**
1. `/ask` page: user types a natural-language request ("invest in NVDA", "hedge the book").
2. The request is parsed (schema-validated) and queued with a `requested_by: user` tag — the SAME pipeline then runs on it. No special treatment: the request still faces analysts, debate, and all 12 gates.
3. The UI shows the user's request → the desk's response verdict, including honest rejections ("Ursa's event-risk argument won; NVDA earnings in 36h").

*The copilot can request analysis; it can never directly order. This is both safe and a better demo.*

## 4. Senti — sentiment analysis spec (per requirements)

**Inputs (per candidate):**
- Alpaca news API: recent articles for the symbol (whitelisted sources)
- Alpaca corporate actions (dividends/splits/mergers near ex-dates)
- Event calendar context (earnings/FOMC/CPI dates for the symbol/index)
- Social-opinion proxies accessible via the news feed (social chatter surfaced in articles)

**Task:** synthesize public opinion with **source credibility weighting** and **expert-review synthesis**:

```json
// Senti output schema (strict)
{
  "symbol": "NVDA",
  "public_sentiment": {"score": -1.0, "to": 1.0},   // aggregate
  "confidence": 0.68,                                   // 0..1
  "source_breakdown": [
    {"source": "Reuters", "credibility": 0.9, "lean": 0.4, "headline": "..."},
    {"source": "SocialChatter", "credibility": 0.4, "lean": -0.2, "note": "..."}
  ],
  "expert_consensus": {"lean": 0.3, "summary": "Analysts cite..."},
  "event_flags": ["earnings T-36h", "FOMC Thu"],
  "citations": ["url1", "url2"],
  "as_of": "2026-09-03T14:22:00Z"                     // point-in-time discipline
}
```

**Rules:**
- Every claim carries a citation; uncited claims are dropped at schema validation.
- Credibility weights are code-side constants (LLM proposes; code applies).
- Output is timestamped; the desk only ever trades on point-in-time data (no look-ahead).
- Senti is the voice of "public opinion, sources, and expert reviews" in the debate — Toro/Ursa must cite Senti's report, not their own vibes.

## 5. Debate protocol (Toro ↔ Ursa → Verdi)

**Inputs:** the analysts' structured reports (trend/IVR/GEX/liquidity/event-risk) + Senti's sentiment report + any L3 lessons relevant to this symbol/structure.

**Format (2 rounds max — cost discipline):**
- **Round 1:** Toro argues the bull case; Ursa argues the bear case. Each must cite at least 2 analyst facts + 1 sentiment datapoint + (if any) 1 prior lesson. Schema: `{claims: [{fact_ref, argument}], risks: [...], conviction: 0..1}` — claims without `fact_ref` are invalid.
- **Round 2:** rebuttals only — each attacks the other's weakest claim.
- **Verdi (GPT-4o):** verdict `{direction: BULLISH|BEARISH|NEUTRAL, conviction: 0..1, key_factor: "...", weakest_link: "..."}` — with the full transcript attached for the UI's decision cards.

**Guardrails:** researchers cannot introduce new market facts (only re-weight cited ones); Verdi cannot see sizing; the structurer receives verdict only, never raw debate, so personality can't leak into math.

## 6. Structurer (deterministic menu)

Given `verdict + regime + candidate`, code selects from the fixed menu (LLM only confirms or passes):

| Regime \ Verdict | BULLISH | NEUTRAL | BEARISH |
|---|---|---|---|
| Calm (low VIX, IV rich, +GEX) | bull put spread (16–20Δ) | iron condor 16Δ / wheel CSP | bear call spread (16–20Δ) |
| Choppy (VIX 20–30) | smaller size or pass | wheel CSP only | smaller size or pass |
| Stressed (VIX > 35 or −GEX) | PASS | PASS | PASS |

Code picks every strike, wing, DTE, and size (0.5–1% NAV); computes credit/width, POP, expected move; emits the exact order spec. The LLM "confirm/pass" step exists to let a reasoning model veto obviously mis-contextualized structures — it cannot alter terms.

## 7. Sgt. Gate — the 12 gates

Pure code, no opinions. Every verdict journaled with reason codes; none short-circuit (every proposal is scored against all 12 so the journal records *how badly* a rejected trade failed):

1. `SANITY` quotes fresh & prices positive · 2. `REGIME` VIX/GEX router allows the structure · 3. `VRP_EDGE` implied-vs-realized edge ≥ threshold · 4. `EVENT_RISK` no entry inside blackout window · 5. `DEFINED_RISK` atomic mleg, capped loss structural · 6. `LIQUIDITY` leg OI ≥ 250, spread ≤ 25% mid · 7. `CREDIT_QUALITY` credit ≥ 15% of width · 8. `POSITION_SIZE` ≤ 1% NAV · 9. `PORTFOLIO_RISK` total ≤ 5% NAV · 10. `CONCENTRATION` ≤ 2 structures/underlying · 11. `DUPLICATE` deterministic client_order_id · 12. `DAILY_HALT` day P&L > −2% NAV → flatten & stand down.

## 8. Sage — post-mortem & self-improvement spec (per requirements)

**Trigger (configurable, see RISK.md):** an open position's unrealized P&L ≤ **−8%** of premium risked **but above the hard stop** (2× credit) — "down by a threshold, but above the kill line" — OR any position closed at a loss ≥ 50% of max risk.

**The post-mortem run:**
1. Assemble the file: entry decision card (thesis, verdict, conviction), the debate transcript, Senti's report as-of entry, the exit rules in force, the actual price/IV path since entry.
2. GPT-4o Sage answers a fixed rubric (schema-validated):
   - `root_cause`: one of `{thesis_wrong, event_risk_underweighted, timing_bad, regime_shift, luck}` — "why the prediction failed"
   - `failed_signal`: which specific input (trend? sentiment? IVR?) pointed the wrong way
   - `missed_check`: what the desk should have examined but didn't
   - `lesson`: one sentence, actionable, checkable ("block premium-selling within 24h of CPI when IVR < 25")
   - `param_proposal`: optional tightening, e.g. `{"event_blackout_hours": 24 → 36}` — **restrict-only**
3. A deterministic validator enforces: lesson is boolean-checkable against future candidates; param proposals may only move in the tightening direction and within hardcoded bounds (see RISK.md §3); anything else is journaled as `REJECTED_PROPOSAL`.
4. The lesson is written to **L3 memory** with a back-reference to the losing trade; param proposals enter a review queue and apply only after the next cycle starts (logged, reversible from config history).
5. The UI gets a **Post-mortem card** (Sage's mascot goes `post-mortem` state: mirror → lightbulb): "Trade #12 lost 0.8% NAV. Root cause: event risk underweighted. Lesson learned — see it applied on the next CPI-adjacent candidate." This is the "desk visibly learns" moment.

## 9. Memory spec (the K in STONKS)

| Layer | Write path | Read path | Decay |
|---|---|---|---|
| **L1** snapshots | every cycle: prices, VIX, IVR, screener set | analysts (current cycle), post-mortems (what did the world look like) | 24h rolling |
| **L2** ledger | on entry: full decision card + exit rules | exit ladder, Sage (thesis ref), UI positions | life of position |
| **L3** lessons | Sage post-mortems only | **injected into every debate prompt + structurer context**; UI `/memory` | near-permanent (cap 50, oldest merged) |

**Self-improvement closure:** L3 lessons are the only LLM-written memory, and they can only *restrict* future behavior — the desk can get more careful, never more reckless. That asymmetry is the safety story we tell judges.

## 10. Narrator (Prime)

Gemini Flash converts journal entries into one-line, human sentences for the feed and the mascot captions ("Senti is reading 14 NVDA articles — 3 of them mention the earnings call"). It can only rephrase journaled facts. No narration ever contains numbers that aren't in the journal (provenance by construction).

## 11. Cost & latency budget

| Call | Model | Per cycle |
|---|---|---|
| Senti (×≤3 candidates) | Gemini Flash | 3 |
| Debate (2 researchers × 2 rounds) | Gemini Flash | 4 |
| Verdi verdict | GPT-4o | 1 |
| Structurer confirm | GPT-4o | 1 (only when a structure exists) |
| Sage post-mortem | GPT-4o | on trigger only |
| Narrator | Gemini Flash | ~2 (batched) |
| **Total** | | **≤ 8–12 calls/cycle**, analyst reports cached intraday |

## 12. Testability

- Every agent has a deterministic fixture path (recorded LLM responses for tests) — no test hits a live LLM.
- Gates have property-based tests (random structures must always satisfy capped-loss invariants).
- Debate transcripts are replayable from the journal (same inputs → same journal rendering).
- The full pipeline has a "replay yesterday" mode using L1 snapshots — also the source of any post-hoc stats for the write-up.
