"""Structurer confirm (AGENTS.md §6) — GPT-4o may only confirm or pass."""
from __future__ import annotations

from stonks.agents.llm import LLMClient, LLMBusError
from stonks.schemas import Regime, StructureSpec, Verdict

SYSTEM = (
    "You are the final check on a structured options trade. The terms are computed "
    "by deterministic code and CANNOT be altered. Judge only whether the structure "
    "is contextually sane for the regime and verdict. Respond ONLY with JSON: "
    '{"decision": "confirm"|"pass", "reason": str}.'
)


async def confirm(
    spec: StructureSpec | None,
    regime: Regime,
    verdict: Verdict,
    llm: LLMClient | None = None,
) -> tuple[bool, str]:
    if spec is None:
        return False, "no structure"
    llm = llm or LLMClient()
    user = (
        f"Regime: {regime.summary}\nVerdict: {verdict.direction} ({verdict.conviction:.2f})\n"
        f"Structure: {spec.kind} on {spec.symbol}, {spec.contracts} contracts, "
        f"credit {spec.credit}, width {spec.width}, DTE {spec.dte}, max loss {spec.max_loss}."
    )
    try:
        data = await llm.complete("structurer", SYSTEM, user)
        decision = str(data.get("decision", "confirm")).lower()
        reason = str(data.get("reason", ""))[:200] or data.get("_model", "")
        return decision == "confirm", reason
    except LLMBusError:
        return True, "deterministic pass"
