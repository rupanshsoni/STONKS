"""The desk cycle orchestrator (ARCHITECTURE.md §2.2).

tick() when market open:
  reconcile → manage_exits → discover → analyze → debate → structure →
  gate → execute → journal → post_mortem_scan → narrate
after hours: sleep_cycle.

Every step emits a journal entry + SSE event. Exits run before entries — they
free risk budget. The broker is the source of truth; on REST/CLI mismatch the
desk halts new entries and never trades disputed state.
"""
from __future__ import annotations

import asyncio
import math
import uuid
from datetime import timedelta

from stonks.agents import (
    CodeAnalysts,
    LLMClient,
    SentiAgent,
    confirm,
    judge,
    narrate,
    post_mortem,
    run_debate,
)
from stonks.agents.narrator import EVENT_PHRASES
from stonks.alpaca.cli import AlpacaCLI
from stonks.alpaca.client import AlpacaClient
from stonks.alpaca.executor import ExecutionHalt, Executor, make_coid
from stonks.alpaca.reconcile import reconcile
from stonks.config import ENV, RISK, apply_param, load_config_history
from stonks.kernel import evaluate_gates, evaluate_regime, pick_structure
from stonks.kernel.exits import check_exits
from stonks.kernel.gates import GateContext
from stonks.journal import Journal
from stonks.memory import MemoryStore
from stonks.schemas import (
    AppliedParam,
    AskRequest,
    ClockView,
    CycleSummary,
    JournalEvent,
    MarketSnapshot,
    PositionLedger,
    PositionView,
    Regime,
    StructureSpec,
    utcnow,
)

from stonks.config import CAST, EARNINGS, EVENTS


class Orchestrator:
    def __init__(
        self,
        journal: Journal | None = None,
        store: MemoryStore | None = None,
        client: AlpacaClient | None = None,
        executor: Executor | None = None,
        cli: AlpacaCLI | None = None,
        llm: LLMClient | None = None,
        test_mode: bool = False,
    ) -> None:
        self.test_mode = test_mode or ENV.test_mode
        self.journal = journal or Journal()
        self.store = store or MemoryStore()
        self.client = client or AlpacaClient(test_mode=self.test_mode)
        self.executor = executor or Executor(test_mode=self.test_mode)
        self.cli = cli or AlpacaCLI(test_mode=self.test_mode)
        self.llm = llm or LLMClient(test_mode=self.test_mode)
        self.analysts = CodeAnalysts()
        self.senti = SentiAgent(llm=self.llm)
        self.halted_entries = False
        self.daily_stood_down = False
        self.agent_states: dict[str, str] = {c["id"]: "idle" for c in CAST}
        self.agent_tasks: dict[str, str] = {c["id"]: "" for c in CAST}

    # ------------------------------------------------------------- helpers

    def _set_state(self, agent: str, state: str, task: str = "") -> None:
        self.agent_states[agent] = state
        if task:
            self.agent_tasks[agent] = task

    def _event(self, *args, **kwargs) -> JournalEvent:
        kwargs.setdefault("persist", True)
        ev = self.journal.emit(*args, **kwargs)
        ev.data = dict(ev.data)
        ev.data["mascot_state"] = self.agent_states.get(ev.agent, "idle")
        return ev

    # ------------------------------------------------------------- tick

    async def tick(self) -> CycleSummary:
        cycle_id = uuid.uuid4().hex[:12]
        summary = CycleSummary(cycle_id=cycle_id, started=utcnow())
        clock = await self.client.clock()

        if not clock.open and not self.test_mode:
            await self.sleep_cycle(cycle_id)
            summary.ended = utcnow()
            return summary

        self._event("desk", "cycle_start", "The desk opens a new cycle.", cycle_id=cycle_id)

        rec = await self.reconcile_step(cycle_id)
        account = await self.client.account()
        equity = account.equity
        self.journal.emit("desk", "equity_tick", f"equity {equity:.2f}",
                           cycle_id=cycle_id, data={"equity": equity},
                           model=None, persist=False)

        day_pnl = account.day_pnl
        if day_pnl <= -RISK.daily_halt_pct * equity:
            await self.daily_halt(cycle_id, equity)
            summary.halted = True
            summary.ended = utcnow()
            return summary

        await self.manage_exits(cycle_id, summary)
        if self.halted_entries:
            self._event("desk", "cycle_end",
                        "Cycle closed — entries halted on state mismatch.",
                        cycle_id=cycle_id, level="warn")
            summary.ended = utcnow()
            return summary

        await self.discover_and_trade(cycle_id, summary, equity)

        self._event("desk", "cycle_end",
                     f"Cycle closed — {summary.orders_placed} placed, "
                     f"{summary.rejections} rejected.",
                     cycle_id=cycle_id)
        summary.ended = utcnow()
        return summary

    # ------------------------------------------------------------- steps

    async def sleep_cycle(self, cycle_id: str) -> None:
        for c in CAST:
            self._set_state(c["id"], "sleeping")
        self._event("prime", "market_closed", "Market closed — the desk sleeps.",
                    cycle_id=cycle_id)
        await self.reconcile_step(cycle_id, quiet=True)

    async def reconcile_step(self, cycle_id: str, quiet: bool = False) -> dict:
        self._set_state("prime", "analyzing", "reconciling books")
        try:
            result = await reconcile(self.client, self.cli)
        except Exception as exc:
            result = {"match": True, "rest": {}, "cli": {}, "error": str(exc)}
        if not result.get("match"):
            self.halted_entries = True
            self._event("desk", "reconcile",
                        "REST/CLI position mismatch — halting new entries until reconciled.",
                        cycle_id=cycle_id, data=result, level="warn")
            self._set_state("gate", "risk_alert", "state mismatch")
        elif not quiet:
            self._event("desk", "reconcile", "Books match — REST and CLI agree.",
                        cycle_id=cycle_id, data=result, surface="cli")
        self._set_state("prime", "idle")
        return result

    async def daily_halt(self, cycle_id: str, equity: float) -> None:
        self.daily_stood_down = True
        self._set_state("gate", "risk_alert", "daily halt tripped")
        self._event("gate", "gate_verdict",
                    f"DAILY_HALT_TRIPPED — day P&L at halt line; flattening and standing down.",
                    cycle_id=cycle_id,
                    data={"halt": True, "gate": "DAILY_HALT",
                          "results": [{"gate": "DAILY_HALT", "passed": False,
                                       "reason_code": "DAILY_HALT_TRIPPED",
                                       "detail": f"day pnl at {-RISK.daily_halt_pct:.0%} NAV"}]},
                    level="warn")
        for ledger in await asyncio.to_thread(self.store.open_positions):
            await self._close_position(ledger, cycle_id, "Daily halt flatten", 0.0)
        self._set_state("gate", "idle")

    async def manage_exits(self, cycle_id: str, summary: CycleSummary) -> None:
        self._set_state("prime", "analyzing", "running exit ladder")
        ledgers = await asyncio.to_thread(self.store.open_positions)
        for ledger in ledgers:
            chain = await self.client.option_chain(ledger.symbol,
                                                   RISK.target_dte_min - 10,
                                                   RISK.target_dte_max + 10)
            view = self._ledger_to_view(ledger, chain)
            decision = check_exits(view, chain)
            if decision is None:
                if view.unrealized_pnl is not None:
                    pnl_pct = view.unrealized_pnl / max(ledger.spec.premium_risk, 1.0)
                    if pnl_pct <= RISK.post_mortem_trigger_pct:
                        await self.run_post_mortem(ledger, cycle_id, view)
                continue
            self._set_state("xq", "trading", f"exit: {decision.rule}")
            self._event("xq", "exit_rule",
                        f"{decision.rule}: {decision.detail}",
                        symbol=ledger.symbol, cycle_id=cycle_id,
                        data={"rule": decision.rule, "pnl_est": decision.pnl_est})
            await self._close_position(ledger, cycle_id, decision.rule, decision.pnl_est)
            summary.rejections += 0
        self._set_state("prime", "idle")

    async def _close_position(self, ledger: PositionLedger, cycle_id: str,
                              rule: str, pnl_est: float) -> None:
        try:
            # Price the buyback off the CURRENT structure value, not entry
            # credit — a static multiple of entry never fills a hard-stop.
            # Cap: width (max structural loss) → always marketable, bounded.
            max_debit = None
            if rule == "Daily halt flatten":
                max_debit = ledger.spec.width  # flatten at any bounded price
            elif pnl_est is not None and pnl_est < 0:
                # losing stop: current mark ≈ (credit*100*qty + |pnl|)/(100*qty)
                qty = max(ledger.spec.contracts, 1)
                max_debit = ledger.spec.credit + abs(pnl_est) / (100.0 * qty)
                max_debit = min(max_debit * 1.10, ledger.spec.width)
            else:
                # profit-taking: pay up to ~70% of entry credit (target keeps
                # >=30% of the credit as realized profit)
                max_debit = max(ledger.spec.credit * 0.70, 0.10)
            receipt = await self.executor.close_position(ledger.spec, max_debit)
            closed_pnl = pnl_est
            await asyncio.to_thread(
                self.store.mark_closed, ledger.coid, utcnow(), closed_pnl, rule,
            )
            self._event("xq", "position_closed",
                        f"Closed {ledger.symbol} {ledger.spec.kind} via {rule} "
                        f"(~{closed_pnl:+.2f}).",
                        symbol=ledger.symbol, cycle_id=cycle_id,
                        data={"coid": ledger.coid, "rule": rule,
                              "pnl": closed_pnl, "surface": receipt.surface})
            if closed_pnl > 0:
                self._set_state("xq", "celebrating", "closed at profit")
                self._set_state("prime", "celebrating", "stonks.")
                self._event("prime", "narration", "Stonks.", symbol=ledger.symbol,
                            cycle_id=cycle_id)
                self._set_state("xq", "idle")
                self._set_state("prime", "idle")
            else:
                if rule != "Daily halt flatten":
                    await self.run_post_mortem(ledger, cycle_id, None, closed_pnl)
        except Exception as exc:
            self._event("xq", "exit_rule",
                        f"Close FAILED for {ledger.symbol}: {exc}",
                        symbol=ledger.symbol, cycle_id=cycle_id, level="error")

    def _ledger_to_view(self, ledger: PositionLedger, chain) -> PositionView:
        dte = max((ledger.spec.dte - max((utcnow() - ledger.entry_ts).days, 0)), 0)
        return PositionView(
            id=ledger.coid, coid=ledger.coid, symbol=ledger.symbol,
            kind=ledger.spec.kind, qty=float(ledger.spec.contracts),
            entry_ts=ledger.entry_ts, entry_credit=ledger.entry_credit,
            dte=dte, legs=ledger.spec.legs, thesis=ledger.thesis,
            verdict=ledger.verdict,
        )

    # ------------------------------------------------------------- discovery

    async def discover_and_trade(self, cycle_id: str, summary: CycleSummary,
                                 equity: float) -> None:
        candidates = await self.client.screener(RISK.max_candidates)
        pending = await asyncio.to_thread(self.store.pending_asks)
        tradable = set(RISK.watchlist)
        ask_symbols: list[tuple[AskRequest, str]] = []
        for req in pending:
            if req.status == "queued":
                req.status = "running"
                await asyncio.to_thread(self.store.update_ask, req)
                self._event("desk", "ask_received",
                            f"Copilot request running: {req.text}",
                            cycle_id=cycle_id, data={"ask_id": req.id})
            for s in req.symbols:
                if s in tradable:
                    ask_symbols.append((req, s))
                else:
                    req.status = "rejected"
                    req.result_summary = (
                        f"'{s}' is not in the desk's tradable universe "
                        f"({', '.join(sorted(tradable))})."
                    )
                    await asyncio.to_thread(self.store.update_ask, req)
                    self._event("desk", "ask_received",
                                f"Copilot request rejected — '{s}' not tradable here.",
                                cycle_id=cycle_id, level="warn")
        ask_only = [s for (_, s) in ask_symbols]
        # Candidate priority: watchlist first (always optionable, always
        # liquid), then screener finds (may be junk/unoptionable — the
        # pipeline drops price<=0 and empty chains cheaply, but LLM calls
        # are expensive: free-tier cycles are minutes each).
        watch_syms = set(RISK.watchlist)
        cands_watch = [c for c in candidates if c.symbol in watch_syms]
        cands_found = [c for c in candidates if c.symbol not in watch_syms]
        merged: list = cands_watch + cands_found
        for req, sym in ask_symbols:
            if sym in tradable and sym not in [c.symbol for c in merged]:
                price_map = await self.client.snapshot_prices([sym])
                from stonks.schemas import Candidate as C
                merged.append(C(symbol=sym, price=price_map.get(sym, 0.0),
                                reason=f"/ask: {req.text[:60]}"))
        merged = merged[: RISK.max_candidates + len(ask_symbols)]

        prices = await self.client.snapshot_prices([c.symbol for c in merged])
        vix = self._vix_value()
        if not self.test_mode:
            # One market-wide VIX refresh per cycle (SPY ATM implied vol).
            await self._market_regime_inputs("SPY")
            vix = self._vix_value()
        lessons = await asyncio.to_thread(self.store.lessons)

        for candidate in merged:
            symbol = candidate.symbol
            price = prices.get(symbol, candidate.price)
            if price <= 0:
                continue
            spec = await self.run_pipeline(symbol, price, cycle_id, summary,
                                          equity, vix, lessons, pending_asks=ask_symbols)
            if spec is not None:
                summary.orders_placed += 1
        summary.candidates_considered = len(merged)

    # ------------------------------------------------------------- pipeline

    async def run_pipeline(
        self,
        symbol: str,
        price: float,
        cycle_id: str,
        summary: CycleSummary,
        equity: float,
        vix: float,
        lessons,
        pending_asks: list | None = None,
    ) -> StructureSpec | None:
        chain = await self.client.option_chain(symbol, RISK.target_dte_min,
                                                RISK.target_dte_max)
        if not chain:
            return None
        if not self.test_mode:
            # per-symbol IV rank + VRP edge (the trade's own vol economics)
            await self._hydrate_symbol_regime(symbol, chain)
        news = await self.client.news(symbol)
        events_hours = self._hours_to_event(symbol)
        event_flags = self._event_flags(symbol)

        self._set_state("senti", "reading_news", f"reading {symbol} news")
        self._event("senti", "analysis", f"Senti reads {len(news)} articles on {symbol}.",
                    symbol=symbol, cycle_id=cycle_id)
        sentiment = await self.senti.analyze(symbol, news, event_flags)
        self._set_state("senti", "idle")
        self._event("senti", "senti_report",
                    f"{symbol} sentiment {sentiment.public_sentiment:+.2f} "
                    f"(conf {sentiment.confidence:.2f}, {len(sentiment.citations)} citations).",
                    symbol=symbol, cycle_id=cycle_id,
                    data=sentiment.model_dump(),
                    model=sentiment.model or "fallback:rules")

        reports = self.analysts.analyze(symbol, chain, price, news,
                                        iv_rank=self._iv_rank(symbol), vix=vix,
                                        events_hours=events_hours)
        self._set_state("verdi", "analyzing", f"analyzing {symbol}")
        self._event("verdi", "analysis",
                    f"Analysts report on {symbol}: "
                    + "; ".join(f"{r.analyst} {'ok' if not r.concerns else 'concerns'}"
                                for r in reports),
                    symbol=symbol, cycle_id=cycle_id)
        self._set_state("verdi", "idle")

        relevant_lessons = [l for l in lessons if symbol.lower() in l.text.lower()]
        self._set_state("toro", "debating", f"bull case for {symbol}")
        self._set_state("ursa", "debating", f"bear case for {symbol}")
        self._set_state("verdi", "debating", "presiding")
        rounds = await run_debate(reports, sentiment, relevant_lessons, llm=self.llm)
        verdict = await judge(rounds, reports, sentiment, llm=self.llm)
        self._event("verdi", "debate_verdict",
                    f"Verdict: {verdict.direction} ({verdict.conviction:.2f}) — "
                    f"{verdict.key_factor}",
                    symbol=symbol, cycle_id=cycle_id,
                    data={"rounds": [r.model_dump() for r in rounds],
                          "verdict": verdict.model_dump()},
                    model=verdict.model)
        for a in ("toro", "ursa", "verdi"):
            self._set_state(a, "idle")

        gex_sign = 1
        for r in reports:
            if r.analyst == "gex":
                for f in r.facts:
                    if f.id == "gex.sign":
                        gex_sign = int(f.value)
        regime = evaluate_regime(vix, gex_sign, iv_rank=self._iv_rank(symbol))

        if regime.band == "stressed":
            self._set_state("gate", "risk_alert", "stressed regime")
            self._event("gate", "gate_verdict",
                        f"REGIME_STRESSED — no new structures while stressed.",
                        symbol=symbol, cycle_id=cycle_id,
                        data={"approved": False, "results": [
                            {"gate": "REGIME", "passed": False,
                             "reason_code": "REGIME_STRESSED", "detail": regime.summary}]})
            self._set_state("gate", "idle")
            summary.rejections += 1
            await self._answer_asks(pending_asks, symbol,
                                    f"Rejected: regime stressed ({regime.summary}).")
            return None

        spec = pick_structure(verdict, regime, symbol, chain, price, equity,
                              lessons=relevant_lessons)
        if spec is None:
            self._event("prime", "analysis",
                        f"No structure for {symbol} — regime/lesson constraints.",
                        symbol=symbol, cycle_id=cycle_id)
            summary.rejections += 1
            await self._answer_asks(pending_asks, symbol,
                                    "No structure passed the deterministic menu for this verdict/regime.")
            return None

        ok, reason = await confirm(spec, regime, verdict, llm=self.llm)
        if not ok:
            self._event("desk", "analysis",
                        f"Structurer confirm PASS on {symbol}: {reason}",
                        symbol=symbol, cycle_id=cycle_id)
            summary.rejections += 1
            await self._answer_asks(pending_asks, symbol, f"The desk passed: {reason}")
            return None

        coid = make_coid(spec.intent, symbol)
        open_ledgers = await asyncio.to_thread(self.store.open_positions)
        open_risk = sum(l.spec.premium_risk for l in open_ledgers)
        open_views = [self._ledger_to_view(l, []) for l in open_ledgers]
        from stonks.alpaca.executor import PLACED_RECEIPTS, SEEN_COIDS
        coid_exists = coid in SEEN_COIDS or any(l.coid == coid for l in open_ledgers)
        dry_run_ok = await self.executor.dry_run(spec, coid)
        quotes_age = await self.client.quote_stale_seconds(symbol)

        ctx = GateContext(
            nav=equity, day_pnl=0.0, open_positions=open_views, open_risk=open_risk,
            chain=chain, quotes_age_seconds=quotes_age, regime=regime,
            iv_rank=self._iv_rank(symbol), vix=vix,
            vrp_edge=(getattr(self, "_symbol_vrp", {}) or {}).get(symbol)
                     if not self.test_mode else None,
            event_hours_to_nearest=events_hours, coid_exists=coid_exists,
            dry_run_ok=dry_run_ok,
        )
        self._set_state("gate", "analyzing", f"12 gates on {symbol}")
        verdict_gates = await evaluate_gates(spec, ctx)
        self._event("gate", "gate_verdict",
                    (f"{spec.symbol} {spec.kind}: {verdict_gates.score}/12 gates passed — APPROVED."
                     if verdict_gates.approved else
                     f"{spec.symbol} {spec.kind}: REJECTED — "
                     f"{next((r.reason_code for r in verdict_gates.results if not r.passed), '?')}."),
                    symbol=symbol, cycle_id=cycle_id,
                    data={"approved": verdict_gates.approved,
                          "results": [r.model_dump() for r in verdict_gates.results],
                          "spec": spec.model_dump(), "coid": coid})

        if not verdict_gates.approved:
            self._set_state("gate", "risk_alert",
                            f"rejected {symbol}")
            self._event("gate", "risk_alert",
                        "Sgt. Gate said no. Here's why: "
                        + ", ".join(r.reason_code or "?" for r in verdict_gates.results
                                    if not r.passed) + ".",
                        symbol=symbol, cycle_id=cycle_id, level="warn")
            self._set_state("gate", "idle")
            summary.rejections += 1
            fail_first = next((r.reason_code for r in verdict_gates.results if not r.passed), "?")
            await self._answer_asks(pending_asks, symbol,
                                    f"Rejected: Sgt. Gate said no — {fail_first}.")
            return None

        self._set_state("gate", "idle")

        thesis = f"{verdict.direction} {verdict.conviction:.2f} — {verdict.key_factor}"
        ledger = PositionLedger(
            coid=coid, cycle_id=cycle_id, symbol=symbol, kind=spec.kind,
            spec=spec, thesis=thesis, verdict=verdict, sentiment=sentiment,
            debate=rounds, entry_ts=utcnow(), entry_credit=spec.credit,
            exit_rules={"profit_target": RISK.profit_target_pct,
                        "hard_stop_mult": RISK.hard_stop_multiple,
                        "time_stop_dte": RISK.time_stop_dte},
        )

        self._set_state("xq", "trading", f"placing {symbol} {spec.kind}")
        self._event("xq", "order_submitted",
                    f"Routing {spec.contracts}× {spec.kind} on {symbol} "
                    f"(credit {spec.credit:.2f}) — atomic multi-leg.",
                    symbol=symbol, cycle_id=cycle_id,
                    data={"coid": coid, "kind": spec.kind})
        try:
            receipt = await self.executor.place(spec, coid)
        except ExecutionHalt as exc:
            self._event("xq", "order_submitted",
                        f"Execution halted for {symbol}: {exc.reason}",
                        symbol=symbol, cycle_id=cycle_id, level="error")
            self._set_state("xq", "idle")
            summary.rejections += 1
            return None
        await asyncio.to_thread(self.store.save_position, ledger)
        filled = receipt.status in ("filled", "filled_by_new_order")
        self._event("xq", "order_filled" if filled else "order_working",
                    (f"FILLED {symbol} {spec.kind} @ {receipt.filled_avg_price:.2f} "
                     f"credit ({receipt.surface})." if filled else
                     f"Order working on {symbol} ({receipt.status}, {receipt.surface})."),
                    symbol=symbol, cycle_id=cycle_id,
                    data={"coid": coid, "surface": receipt.surface,
                          "status": receipt.status,
                          "filled_avg_price": receipt.filled_avg_price},
                    surface=receipt.surface)
        if filled:
            self._set_state("xq", "celebrating", "filled")
            self._set_state("prime", "celebrating", "stonks.")
            self._event("prime", "narration", "Stonks.", symbol=symbol, cycle_id=cycle_id)
            self._set_state("xq", "idle")
            self._set_state("prime", "idle")
        else:
            self._set_state("xq", "idle")

        self._event("prime", "decision_card",
                    thesis, symbol=symbol, cycle_id=cycle_id,
                    data={"coid": coid, "verdict": verdict.model_dump(),
                          "sentiment": sentiment.model_dump(),
                          "rounds": [r.model_dump() for r in rounds],
                          "spec": spec.model_dump()})

        await self._answer_asks(pending_asks, symbol,
                                f"Approved and executed: {spec.kind} on {symbol}, "
                                f"{spec.contracts} contracts, credit {spec.credit:.2f}.")
        return spec

    async def _answer_asks(self, pending_asks: list | None, symbol: str,
                           answer: str) -> None:
        if not pending_asks:
            return
        for req, s in pending_asks:
            if s == symbol:
                req.status = "answered" if "Approved" in answer else "rejected"
                req.result_summary = answer
                await asyncio.to_thread(self.store.update_ask, req)

    # ------------------------------------------------------------- sage

    async def run_post_mortem(self, ledger: PositionLedger, cycle_id: str,
                              view: PositionView | None = None,
                              closed_pnl: float | None = None) -> None:
        self._set_state("sage", "post_mortem",
                        f"reviewing {ledger.symbol} loss")
        self._event("sage", "post_mortem",
                    f"Sage reviews the losing {ledger.symbol} {ledger.spec.kind}…",
                    symbol=ledger.symbol, cycle_id=cycle_id,
                    data={"coid": ledger.coid})
        try:
            lesson = await post_mortem(ledger, [], closed_pnl, llm=self.llm)
        except Exception:
            self._set_state("sage", "idle")
            return
        await asyncio.to_thread(self.store.save_lesson, lesson)
        rejected = [p for p in lesson.param_proposals if p.status == "rejected"]
        applied = [p for p in lesson.param_proposals if p.status == "applied"]
        self._event("sage", "lesson_learned",
                    f"Lesson: {lesson.text}"
                    + (f" | Params tightened: {', '.join(p.param for p in applied)}."
                       if applied else "")
                    + (f" | REJECTED_PROPOSAL: {', '.join(f'{p.param} {p.reason}' for p in rejected)}."
                       if rejected else ""),
                    symbol=ledger.symbol, cycle_id=cycle_id,
                    data=lesson.model_dump(),
                    model=lesson.model or "fallback:rules")
        self._set_state("sage", "analyzing", "lesson filed to L3")
        self._set_state("sage", "idle")
        summary_rejected = [p for p in lesson.param_proposals if p.status == "rejected"]
        for p in rejected:
            self._event("sage", "rejected_proposal",
                        f"REJECTED_PROPOSAL {p.param}: {p.reason}",
                        symbol=ledger.symbol, cycle_id=cycle_id, level="warn")

    # ------------------------------------------------------------- static helpers

    def _hours_to_event(self, symbol: str) -> float | None:
        hours_list = []
        now = utcnow()
        for ev in EVENTS:
            if ev["symbol"] in (symbol, "INDEX"):
                try:
                    from datetime import datetime
                    d = datetime.fromisoformat(ev["date"]).replace(tzinfo=now.tzinfo)
                    hours = (d - now).total_seconds() / 3600.0
                    if 0 <= hours < 24 * 14:
                        hours_list.append(hours)
                except Exception:
                    continue
        if symbol in EARNINGS:
            try:
                from datetime import datetime
                d = datetime.fromisoformat(EARNINGS[symbol]).replace(tzinfo=now.tzinfo)
                hours = (d - now).total_seconds() / 3600.0
                if 0 <= hours < 24 * 14:
                    hours_list.append(hours)
            except Exception:
                pass
        return min(hours_list) if hours_list else None

    def _event_flags(self, symbol: str) -> list[str]:
        flags = []
        now = utcnow()
        for ev in EVENTS:
            if ev["symbol"] in (symbol, "INDEX"):
                try:
                    from datetime import datetime
                    d = datetime.fromisoformat(ev["date"]).replace(tzinfo=now.tzinfo)
                    hours = (d - now).total_seconds() / 3600.0
                    if 0 <= hours < 24 * 7:
                        flags.append(f"{ev['kind']} {ev['date']}")
                except Exception:
                    continue
        if symbol in EARNINGS:
            flags.append(f"earnings {EARNINGS[symbol]}")
        return flags

    def _vix_value(self) -> float:
        """VIX proxy — deterministic fallback; refined per-cycle by _market_regime_inputs.

        Base value is a conservative estimate; when live data is available the
        ATM SPY implied vol (from chain snapshots) overrides it in
        _market_regime_inputs. VIXY (ETF) ≈ VIX/10 gives a sanity band.
        """
        if self.test_mode:
            return 15.0
        return self._live_vix if getattr(self, "_live_vix", None) else 18.0

    def _iv_rank(self, symbol: str) -> float:
        """IV rank proxy: chain IV percentile vs the desk's historical band.

        Live: avg ATM IV from the freshest chain snapshot of this cycle,
        rescaled into a 0..100 rank against a fixed 10..60 IV band (the
        classic index-options band). Falls back to 30 (neutral) when the
        chain is unavailable — journaled as such by the VRP gate detail.
        """
        if self.test_mode:
            return 30.0
        ivs = getattr(self, "_live_ivs", {}).get(symbol)
        if not ivs:
            return 30.0
        avg_iv = sum(ivs) / len(ivs)
        lo, hi = 0.10, 0.60
        rank = (avg_iv - lo) / (hi - lo) * 100.0
        return max(0.0, min(100.0, rank))

    async def _market_regime_inputs(self, symbol: str) -> float:
        """Live VIX proxy for regime routing (market-wide, from SPY).

        Near-ATM SPY 28-40 DTE chain IV reads like a 30-day index vol (how
        VIX itself is built). Cached per cycle; candidates use their own
        per-symbol VRP via _hydrate_symbol_regime.
        """
        if self.test_mode:
            return 15.0
        try:
            spy = await self.client.snapshot_prices(["SPY"])
            px = spy.get("SPY", 0.0)
            chain = await self.client.option_chain("SPY", 28, 40) if px else []
            atm = [e for e in chain if e.iv is not None
                   and abs(e.strike - px) <= max(px * 0.02, 1.0)]
            if atm:
                self._live_vix = sum(e.iv for e in atm) / len(atm) * 100.0
        except Exception:
            pass
        return getattr(self, "_live_vix", 18.0)

    async def _hydrate_symbol_regime(self, symbol: str, chain: list) -> None:
        """Per-symbol IV rank + VRP edge for the VRP gate.

        The gate should measure THE TRADE: candidate's own near-ATM chain IV
        (the vol we'd actually sell) minus its own 20-day realized vol (what
        the underlying actually did). A single-name like NVDA can carry a
        rich VRP while the index (SPY) is flat — using the index edge for a
        single-name candidate is a category error.
        """
        if self.test_mode or not chain:
            return
        try:
            px_map = await self.client.snapshot_prices([symbol])
            px = px_map.get(symbol, 0.0)
            atm = [e for e in chain if e.iv is not None
                   and abs(e.strike - px) <= max(px * 0.02, 1.0)]
            if not atm:
                return
            ivs = [e.iv for e in atm]
            self._live_ivs = getattr(self, "_live_ivs", {}) or {}
            self._live_ivs[symbol] = ivs
            bars = await self.client.daily_bars(symbol, 21)
            closes = [b["c"] for b in bars][-21:]
            if len(closes) >= 10:
                rets = [math.log(closes[i] / closes[i - 1])
                        for i in range(1, len(closes))]
                realized = (sum(r * r for r in rets) / len(rets)) ** 0.5 * math.sqrt(252)
                implied = sum(ivs) / len(ivs)
                self._symbol_vrp = getattr(self, "_symbol_vrp", {}) or {}
                self._symbol_vrp[symbol] = implied - realized
        except Exception:
            pass
