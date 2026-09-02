"""Sage — post-mortem & self-improvement (AGENTS.md §8).

The only LLM-written memory, and it can only RESTRICT future behavior: param
proposals are validated against config.PARAM_BOUNDS (restrict-only) and
anything that would loosen a limit is journaled as REJECTED_PROPOSAL.
"""
from __future__ import annotations

from stonks.agents.llm import LLMClient, LLMBusError
from stonks.config import apply_param, validate_param_proposal
from stonks.schemas import Lesson, ParamProposal, PositionLedger, utcnow

SYSTEM = (
    "You are Sage, the post-mortem analyst of an options trading desk. Review the "
    "losing trade file and answer a fixed rubric. Be specific about which signal "
    "failed. The lesson must be one sentence, actionable, and checkable against "
    "future candidates. Param proposals may only TIGHTEN (restrict) risk limits. "
    "Respond ONLY with JSON: "
    '{"root_cause": "thesis_wrong"|"event_risk_underweighted"|"timing_bad"|"regime_shift"|"luck", '
    '"failed_signal": str, "missed_check": str, "lesson": str, '
    '"param_proposals": [{"param": str, "current": number, "proposed": number}]}. '
    'Valid params: event_blackout_hours, min_iv_rank, max_position_size_pct, '
    'daily_halt_pct, vix_entry_ceiling, vrp_min_edge, min_credit_pct_of_width.'
)

ROOT_CAUSES = {"thesis_wrong", "event_risk_underweighted", "timing_bad", "regime_shift", "luck"}


async def post_mortem(
    ledger: PositionLedger,
    price_path: list[float],
    exit_pnl: float | None,
    llm: LLMClient | None = None,
) -> Lesson:
    llm = llm or LLMClient()
    debate_summary = "; ".join(
        f"[{r.agent}] " + " ".join(c.argument[:80] for c in r.claims) for r in ledger.debate
    )
    user = (
        f"Symbol: {ledger.symbol} | Structure: {ledger.spec.kind} | "
        f"Entry credit: {ledger.entry_credit} | Exit P&L: {exit_pnl}\n"
        f"Thesis: {ledger.thesis}\nVerdict at entry: {ledger.verdict.direction} "
        f"({ledger.verdict.conviction:.2f})\n"
        f"Debate at entry: {debate_summary or 'n/a'}\n"
        f"Sentiment at entry: {ledger.sentiment.public_sentiment if ledger.sentiment else 'n/a'}"
        f" (events: {ledger.sentiment.event_flags if ledger.sentiment else 'n/a'})\n"
        f"Price path since entry: {price_path[:20]}\n"
        f"Exit rules in force: {ledger.exit_rules}\n\nWhy did this prediction fail?"
    )
    try:
        data = await llm.complete("sage", SYSTEM, user)
        root_cause = str(data.get("root_cause", "thesis_wrong"))
        if root_cause not in ROOT_CAUSES:
            root_cause = "thesis_wrong"
        lesson_text = str(data.get("lesson", "")).strip()
        if not lesson_text:
            raise LLMBusError("empty lesson")
        failed_signal = str(data.get("failed_signal", ""))[:120]
        missed_check = str(data.get("missed_check", ""))[:120]
        proposals_raw = data.get("param_proposals", [])
    except LLMBusError:
        root_cause = (
            "event_risk_underweighted"
            if ledger.sentiment and ledger.sentiment.event_flags
            else "thesis_wrong"
        )
        lesson_text = (
            f"Review event proximity and {ledger.spec.kind} terms before next {ledger.symbol} entry."
        )
        failed_signal = "event calendar proximity to entry"
        missed_check = "IV term structure across the event boundary"
        proposals_raw = []

    proposals: list[ParamProposal] = []
    if isinstance(proposals_raw, list):
        for p in proposals_raw:
            if not isinstance(p, dict):
                continue
            param = str(p.get("param", ""))
            try:
                current = float(p.get("current", 0))
                proposed = float(p.get("proposed", 0))
            except (TypeError, ValueError):
                continue
            ok, why = validate_param_proposal(param, current, proposed)
            status = "pending"
            if ok:
                applied = apply_param(param, proposed, motivated_by=ledger.coid)
                status = "applied" if applied else "rejected"
                if not applied:
                    ok = False
            else:
                status = "rejected"
            proposals.append(ParamProposal(
                param=param, current=current, proposed=proposed,
                status=status,  # type: ignore[arg-type]
                reason=why if not ok else "",
            ))

    return Lesson(
        text=lesson_text[:300],
        root_cause=root_cause,  # type: ignore[arg-type]
        failed_signal=failed_signal,
        missed_check=missed_check,
        trade_coid=ledger.coid,
        param_proposals=proposals,
        created_ts=utcnow(),
    )
