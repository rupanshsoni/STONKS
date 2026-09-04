"""Debate protocol (AGENTS.md §5) — Toro the bull, Ursa the bear, Verdi judges.

Researchers may only re-weight cited analyst facts; claims without fact_ref are
dropped at validation. Verdi never sees sizing.
"""
from __future__ import annotations

from stonks.agents.llm import LLMClient, LLMBusError
from stonks.schemas import (
    AnalystReport,
    DebateClaim,
    DebateRound,
    Lesson,
    SentimentReport,
    Verdict,
)

RESEARCHER_SYSTEM = (
    "You are {name}, the {side} researcher of an options trading desk. "
    "Argue the {side} case for the candidate. You MUST cite existing analyst facts "
    "by their fact id (fact_ref) — you cannot introduce new market facts, only "
    "re-weight cited ones. Cite at least 2 analyst facts, 1 sentiment datapoint "
    "(fact_ref 'senti.score' or 'senti.flags'), and any relevant prior lesson. "
    "Respond ONLY with JSON: "
    '{{"claims": [{{"fact_ref": str, "argument": str}}], "risks": [str], "conviction": float 0..1}}.'
)

JUDGE_SYSTEM = (
    "You are Verdi, the judge of an options trading desk debate. Weigh the "
    "researchers' arguments and the cited facts. You never see sizing or strikes. "
    "Respond ONLY with JSON: "
    '{{"direction": "BULLISH"|"BEARISH"|"NEUTRAL", "conviction": float 0..1, '
    '"key_factor": str, "weakest_link": str}}.'
)


def _fact_ids(reports: list[AnalystReport], sentiment: SentimentReport) -> list[str]:
    ids = [f.id for r in reports for f in r.facts]
    ids += ["senti.score", "senti.flags", "senti.experts"]
    return ids


def _lessons_text(lessons: list[Lesson] | None) -> str:
    if not lessons:
        return "none"
    return "; ".join(l.text for l in lessons[:5])


def _clean_round(raw: dict, round_no: int, agent: str, valid_ids: list[str]) -> DebateRound:
    claims = []
    for c in raw.get("claims", []):
        if not isinstance(c, dict):
            continue
        ref = str(c.get("fact_ref", ""))
        arg = str(c.get("argument", ""))
        if ref and arg:
            claims.append(DebateClaim(fact_ref=ref, argument=arg[:400]))
    claims = [c for c in claims if c.fact_ref in valid_ids or c.fact_ref.startswith("senti")]
    try:
        conviction = max(0.0, min(1.0, float(raw.get("conviction", 0.5))))
    except (TypeError, ValueError):
        conviction = 0.5
    return DebateRound(
        round=round_no, agent=agent,  # type: ignore[arg-type]
        claims=claims,
        risks=[str(r)[:200] for r in raw.get("risks", [])][:5],
        conviction=conviction,
    )


def _fallback_claims(reports: list[AnalystReport], sentiment: SentimentReport) -> list[str]:
    ids = [f.id for r in reports for f in r.facts]
    if not ids:
        ids = ["senti.score", "senti.flags"]
    return ids


async def run_debate(
    reports: list[AnalystReport],
    sentiment: SentimentReport,
    lessons: list[Lesson] | None = None,
    llm: LLMClient | None = None,
) -> list[DebateRound]:
    llm = llm or LLMClient()
    valid_ids = _fact_ids(reports, sentiment)
    facts_text = "\n".join(
        f"- {f.id}: {f.label} = {f.value}" for r in reports for f in r.facts
    )
    senti_text = (
        f"- senti.score: {sentiment.public_sentiment} (confidence {sentiment.confidence})\n"
        f"- senti.flags: {sentiment.event_flags}\n"
        f"- senti.experts: {sentiment.expert_consensus.lean if sentiment.expert_consensus else 'n/a'}"
    )
    base_user = (
        f"Analyst facts:\n{facts_text}\nSentiment datapoints:\n{senti_text}\n"
        f"Prior lessons:\n{_lessons_text(lessons)}\nValid fact_refs: {valid_ids}"
    )
    rounds: list[DebateRound] = []

    for name, agent, side in (("Toro", "toro", "bull"), ("Ursa", "ursa", "bear")):
        system = RESEARCHER_SYSTEM.format(name=name, side=side)
        try:
            raw = await llm.complete("debate", system, base_user)
        except LLMBusError:
            claims = _fallback_claims(reports, sentiment)
            rounds.append(DebateRound(
                round=1, agent=agent,  # type: ignore[arg-type]
                claims=[
                    DebateClaim(fact_ref=claims[0] if claims else "senti.score",
                                argument=f"{name} stands {side} on the cited facts (deterministic fallback)."),
                    DebateClaim(fact_ref="senti.score",
                                argument=f"Sentiment reads {sentiment.public_sentiment}; {name} weighs it {side}-ishly."),
                ],
                risks=["deterministic fallback: LLM unavailable"],
                conviction=0.6,
            ))
            continue
        rounds.append(_clean_round(raw, 1, agent, valid_ids))

    r2_inputs = "\n".join(
        f"{r.agent} R{r.round}: " + "; ".join(c.argument[:120] for c in r.claims)
        for r in rounds
    )
    for name, agent in (("Toro", "toro"), ("Ursa", "ursa")):
        system = RESEARCHER_SYSTEM.format(name=name, side="bull" if agent == "toro" else "bear")
        user = f"{base_user}\n\nRound 1 transcript:\n{r2_inputs}\n\nRebut: attack the other side's weakest claim."
        try:
            raw = await llm.complete("debate", system, user)
        except LLMBusError:
            rounds.append(DebateRound(
                round=2, agent=agent,  # type: ignore[arg-type]
                claims=[DebateClaim(
                    fact_ref=valid_ids[0] if valid_ids else "senti.score",
                    argument=f"{name} finds the opposing timing argument weakest (deterministic fallback).",
                )],
                risks=[],
                conviction=0.55,
            ))
            continue
        rounds.append(_clean_round(raw, 2, agent, valid_ids))

    rounds.sort(key=lambda r: (r.round, 0 if r.agent == "toro" else 1))
    return rounds


async def judge(
    rounds: list[DebateRound],
    reports: list[AnalystReport],
    sentiment: SentimentReport,
    llm: LLMClient | None = None,
) -> Verdict:
    llm = llm or LLMClient()
    transcript = "\n".join(
        f"[{r.agent} R{r.round} conv {r.conviction:.2f}] "
        + " | ".join(f"({c.fact_ref}) {c.argument}" for c in r.claims)
        + (f" risks: {'; '.join(r.risks)}" if r.risks else "")
        for r in rounds
    )
    user = f"Debate transcript:\n{transcript}\n\nIssue your verdict."
    try:
        data = await llm.complete("judge", JUDGE_SYSTEM, user)
        direction = str(data.get("direction", "NEUTRAL")).upper()
        if direction not in ("BULLISH", "BEARISH", "NEUTRAL"):
            direction = "NEUTRAL"
        try:
            conviction = max(0.0, min(1.0, float(data.get("conviction", 0.55))))
        except (TypeError, ValueError):
            conviction = 0.55
        return Verdict(
            direction=direction,  # type: ignore[arg-type]
            conviction=conviction,
            key_factor=str(data.get("key_factor", ""))[:200],
            weakest_link=str(data.get("weakest_link", ""))[:200],
            model=data.get("_model", "unknown"),
        )
    except LLMBusError:
        net = 0.0
        total = 0
        for r in rounds:
            weight = 1.0 if r.agent == "toro" else -1.0
            net += weight * r.conviction * max(1, len(r.claims))
            total += 1
        avg = net / max(total, 1)
        direction = "BULLISH" if avg > 0.2 else "BEARISH" if avg < -0.2 else "NEUTRAL"
        return Verdict(
            direction=direction,  # type: ignore[arg-type]
            conviction=0.55,
            key_factor="deterministic rules fallback",
            weakest_link="n/a (fallback)",
            model="fallback:rules",
        )
