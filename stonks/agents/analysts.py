"""Deterministic code analysts (AGENTS.md §1) — no LLM anywhere in this module."""
from __future__ import annotations

from stonks.config import RISK
from stonks.schemas import (
    AnalystReport,
    Fact,
    NewsArticle,
    OptionChainEntry,
)


BULLISH_WORDS = ("surge", "beat", "rally", "gain", "rise", "record", "upgrade", "bullish", "grind higher")
BEARISH_WORDS = ("miss", "fall", "drop", "slump", "warn", "risk", "fear", "bearish", "sell-off")


def _headline_lean(headline: str) -> int:
    h = headline.lower()
    if any(w in h for w in BULLISH_WORDS):
        return 1
    if any(w in h for w in BEARISH_WORDS):
        return -1
    return 0


class CodeAnalysts:
    def analyze(
        self,
        symbol: str,
        chain: list[OptionChainEntry],
        price: float,
        news: list[NewsArticle] | None = None,
        iv_rank: float | None = None,
        vix: float = 15.0,
        events_hours: float | None = None,
    ) -> list[AnalystReport]:
        reports: list[AnalystReport] = []

        news = news or []
        leans = [_headline_lean(a.headline) for a in news]
        news_lean = (sum(leans) / len(leans)) if leans else 0.0
        momentum_note = (
            f"news tone {'positive' if news_lean > 0 else 'negative' if news_lean < 0 else 'neutral'} "
            f"({len(news)} articles, lean {news_lean:+.1f})"
        )
        reports.append(AnalystReport(
            analyst="trend", symbol=symbol,
            facts=[Fact(id="trend.news_lean", label="news tone lean", value=round(news_lean, 2)),
                   Fact(id="trend.articles", label="articles read", value=len(news))],
            summary=momentum_note,
        ))

        reports.append(AnalystReport(
            analyst="ivr", symbol=symbol,
            facts=[Fact(id="ivr.value", label="IV rank", value=iv_rank if iv_rank is not None else "n/a"),
                   Fact(id="ivr.vix", label="VIX", value=round(vix, 1))],
            summary=f"IVR {'available' if iv_rank is not None else 'unavailable'}; VIX {vix:.1f}",
            concerns=[] if (iv_rank is None or iv_rank >= RISK.min_iv_rank) else
            [f"IVR {iv_rank} below floor {RISK.min_iv_rank} — premium selling not paid for"],
        ))

        # Dealer-gamma proxy: gamma-weighted OPEN INTEREST (naive GEX).
        # Raw volume/OI signs are broken proxies on index options —
        # institutional put hedging makes SPY/QQQ/IWM permanently put-heavy
        # by count (verified live: SPY p/c OI 4.2x, still net-long dealer
        # gamma). Weighting by gamma × OI and requiring 2:1 dominance
        # separates genuinely put-gamma-stressed names from normal hedging.
        call_g = sum((e.gamma or 0) * (e.open_interest or 0)
                     for e in chain if e.option_type == "call")
        put_g = sum((e.gamma or 0) * (e.open_interest or 0)
                    for e in chain if e.option_type == "put")
        ratio = call_g / max(put_g, 1.0)
        sign = -1 if ratio < 0.5 else 1
        reports.append(AnalystReport(
            analyst="gex", symbol=symbol,
            facts=[Fact(id="gex.sign", label="gamma-weighted OI sign", value=sign),
                   Fact(id="gex.ratio", label="call/put gamma-OI ratio", value=round(ratio, 2))],
            summary=(f"dealer gamma {'NEGATIVE' if sign < 0 else 'positive'} "
                     f"(call/put gamma-OI {ratio:.2f})"
                     + (" — put gamma dominates ≥2:1" if sign < 0 else "")),
            concerns=["put-gamma dominance ≥2:1 — stressed regime"] if sign < 0 else [],
        ))

        ois = [e.open_interest for e in chain if e.open_interest is not None]
        min_oi = min(ois) if ois else 0
        spreads = [e.spread_pct for e in chain if e.spread_pct is not None]
        max_spread = max(spreads) if spreads else 0.0
        liq_concerns = []
        if min_oi < RISK.min_oi:
            liq_concerns.append(f"min OI {min_oi} < {RISK.min_oi}")
        if max_spread > RISK.max_spread_pct:
            liq_concerns.append(f"max spread {max_spread:.2f} > {RISK.max_spread_pct}")
        reports.append(AnalystReport(
            analyst="liquidity", symbol=symbol,
            facts=[Fact(id="liq.min_oi", label="min OI", value=min_oi),
                   Fact(id="liq.max_spread", label="max spread", value=round(max_spread, 3))],
            summary=f"chain of {len(chain)} contracts; OI floor {RISK.min_oi}, spread cap {RISK.max_spread_pct:.0%}",
            concerns=liq_concerns,
        ))

        event_facts = [Fact(id="event.hours", label="hours to nearest event",
                            value=round(events_hours, 1) if events_hours is not None else "none")]
        flags = [a.headline for a in news if _eventish(a.headline)]
        event_concerns = []
        if events_hours is not None and events_hours < RISK.event_blackout_hours:
            event_concerns.append(f"event in {events_hours:.0f}h — inside {RISK.event_blackout_hours}h blackout")
        reports.append(AnalystReport(
            analyst="event_risk", symbol=symbol,
            facts=event_facts,
            summary=f"nearest event {events_hours}h away" if events_hours is not None else "no known events",
            concerns=event_concerns,
        ))
        return reports


def _eventish(headline: str) -> bool:
    h = headline.lower()
    return any(w in h for w in ("fomc", "cpi", "earnings", "fed", "jobs report", "payrolls"))
