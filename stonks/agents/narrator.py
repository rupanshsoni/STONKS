"""Narrator (AGENTS.md §10) — Gemini Flash rephrases journaled facts only.

No narration ever contains numbers that aren't in the journal (provenance by
construction); the fallback templates are pure functions of the events.
"""
from __future__ import annotations

from stonks.agents.llm import LLMClient, LLMBusError
from stonks.schemas import JournalEvent

SYSTEM = (
    "You are Stonks Prime, narrator of an options trading desk. Turn journal "
    "entries into one short human sentence each, plain confident slightly-memey "
    "but never unserious about risk. Use ONLY numbers that appear in the entries. "
    "Respond ONLY with JSON: {\"lines\": [str, ...]} — one line per event, same order."
)

EVENT_PHRASES: dict[str, str] = {
    "cycle_start": "opened a new cycle",
    "cycle_end": "closed the cycle",
    "analysis": "ran the analysts",
    "senti_report": "read the news",
    "debate_round": "argued the case",
    "debate_verdict": "delivered the verdict",
    "gate_verdict": "checked the gates",
    "order_submitted": "routed the order",
    "order_filled": "got filled",
    "exit_rule": "took the exit",
    "position_closed": "closed the position",
    "post_mortem": "reviewed the loss",
    "lesson_learned": "wrote the lesson down",
    "narration": "said something",
    "market_closed": "went to sleep",
    "reconcile": "checked the books against the broker",
    "ask_received": "took the request",
}


def _fallback_line(e: JournalEvent) -> str:
    verb = EVENT_PHRASES.get(e.type, f"did {e.type}")
    who = e.agent.capitalize() if e.agent != "desk" else "The desk"
    sym = f" on {e.symbol}" if e.symbol else ""
    return f"{who} {verb}{sym}."


async def narrate(
    events: list[JournalEvent],
    llm: LLMClient | None = None,
) -> list[str]:
    if not events:
        return []
    llm = llm or LLMClient()
    payload = "\n".join(
        f"- [{e.agent}] {e.type} {e.symbol or ''}: {e.summary}" for e in events[:12]
    )
    try:
        data = await llm.complete("narrator", SYSTEM, f"Journal entries:\n{payload}")
        lines = [str(x) for x in data.get("lines", [])][: len(events)]
        if not lines:
            raise LLMBusError("no lines")
        return lines
    except LLMBusError:
        return [_fallback_line(e) for e in events]
