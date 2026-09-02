"""Senti — the sentiment analyst (AGENTS.md §4).

Gemini Flash proposes; CODE re-applies credibility weights. Every claim carries
a citation; uncited entries are dropped at validation. Point-in-time discipline:
as_of is stamped by code, never by the model.
"""
from __future__ import annotations

from stonks.agents.llm import LLMClient, LLMBusError
from stonks.config import ENV
from stonks.schemas import (
    ExpertConsensus,
    NewsArticle,
    SentimentReport,
    SourceLean,
    utcnow,
)

SOURCE_CREDIBILITY: dict[str, float] = {
    "Reuters": 0.9,
    "Bloomberg": 0.9,
    "Barron's": 0.8,
    "CNBC": 0.75,
    "MarketWatch": 0.7,
    "SeekingAlpha": 0.4,
}

BULLISH_WORDS = ("surge", "beat", "rally", "gain", "rise", "record", "upgrade", "bullish", "grind higher")
BEARISH_WORDS = ("miss", "fall", "drop", "slump", "warn", "risk", "fear", "bearish", "sell-off")

SYSTEM = (
    "You are Senti, the sentiment analyst of an options trading desk. "
    "Synthesize public opinion about the ticker from the given articles. "
    "Weight sources by credibility. Distinguish expert/analyst opinion from social chatter. "
    "Respond ONLY with JSON matching this schema: "
    '{"symbol": str, "public_sentiment": float in [-1,1], "confidence": float in [0,1], '
    '"source_breakdown": [{"source": str, "lean": float in [-1,1], "headline": str, "note": str}], '
    '"expert_consensus": {"lean": float, "summary": str}, '
    '"event_flags": [str], "citations": [str]}. '
    "cite article urls in citations. No extra keys."
)


def _cred(source: str) -> float:
    return SOURCE_CREDIBILITY.get(source.strip(), 0.5)


def _weighted_mean(breakdown: list[SourceLean]) -> float:
    total_w = 0.0
    total = 0.0
    for s in breakdown:
        w = _cred(s.source)
        total_w += w
        total += w * s.lean
    if total_w == 0:
        return 0.0
    return max(-1.0, min(1.0, total / total_w))


def _fallback(
    symbol: str, articles: list[NewsArticle], events: list[str]
) -> SentimentReport:
    leans: list[SourceLean] = []
    for a in articles:
        h = a.headline.lower()
        lean = 0.0
        if any(w in h for w in BULLISH_WORDS):
            lean = 0.6
        elif any(w in h for w in BEARISH_WORDS):
            lean = -0.6
        leans.append(SourceLean(source=a.source, credibility=_cred(a.source), lean=lean,
                                headline=a.headline, note="deterministic keyword scan"))
    score = _weighted_mean(leans) if leans else 0.0
    return SentimentReport(
        symbol=symbol,
        public_sentiment=round(score, 3),
        confidence=0.4,
        source_breakdown=leans,
        expert_consensus=ExpertConsensus(lean=0.0, summary="Deterministic fallback: neutral"),
        event_flags=events,
        citations=[a.url for a in articles if a.url][:5],
    )


class SentiAgent:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    async def analyze(
        self,
        symbol: str,
        articles: list[NewsArticle],
        events: list[str],
    ) -> SentimentReport:
        if not articles:
            return _fallback(symbol, [], events)
        articles_text = "\n".join(
            f"- [{a.source}] {a.headline} | {a.summary or ''} | {a.url or ''}" for a in articles
        )
        user = (
            f"Ticker: {symbol}\nEvent context: {', '.join(events) or 'none'}\nArticles:\n{articles_text}\n"
            f"Score public sentiment for {symbol}."
        )
        try:
            data = await self.llm.complete("senti", SYSTEM, user)
        except LLMBusError:
            return _fallback(symbol, articles, events)

        model = data.pop("_model", "")
        data.pop("_provider", None)
        breakdown = []
        for s in data.get("source_breakdown", []):
            if not isinstance(s, dict):
                continue
            if not s.get("headline") and not s.get("note"):
                continue
            lean = s.get("lean", 0.0)
            try:
                lean = float(lean)
            except (TypeError, ValueError):
                lean = 0.0
            breakdown.append(SourceLean(
                source=str(s.get("source", "unknown"))[:60],
                credibility=_cred(str(s.get("source", ""))),
                lean=max(-1.0, min(1.0, lean)),
                headline=str(s.get("headline", ""))[:140],
                note=str(s.get("note", ""))[:140],
            ))
        citations = [str(c) for c in data.get("citations", [])][:10]
        citations = [c for c in citations if c.startswith("http") or c] [:10]
        expert = data.get("expert_consensus")
        if isinstance(expert, dict):
            try:
                expert_model = ExpertConsensus(
                    lean=max(-1.0, min(1.0, float(expert.get("lean", 0.0)))),
                    summary=str(expert.get("summary", ""))[:240],
                )
            except (TypeError, ValueError):
                expert_model = ExpertConsensus(lean=0.0, summary="")
        else:
            expert_model = None

        score = _weighted_mean(breakdown) if breakdown else 0.0
        confidence = 0.5
        try:
            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        except (TypeError, ValueError):
            pass
        if not citations:
            confidence *= 0.5

        return SentimentReport(
            symbol=symbol,
            public_sentiment=round(score, 3),
            confidence=round(confidence, 3),
            source_breakdown=breakdown,
            expert_consensus=expert_model,
            event_flags=[str(f) for f in data.get("event_flags", [])][:6],
            citations=citations,
        )
