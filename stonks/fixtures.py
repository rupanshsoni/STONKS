"""Deterministic test fixtures — no test ever hits a live LLM or broker.

These fixtures power STONKS_TEST=true mode (full pipeline, zero network) and
the pytest suite. Subagents MUST make desk code accept these shapes.
"""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent

# ---------------------------------------------------------------- market

ACCOUNT_VIEW = {
    "account_number": "PA-TEST-0001",
    "paper": True,
    "equity": 100000.0,
    "cash": 99000.0,
    "buying_power": 200000.0,
    "day_pnl": 0.0,
    "total_pnl": 0.0,
    "baseline": 100000.0,
    "options_level": 3,
}

CLOCK_OPEN = {"open": True, "phase": "open"}
CLOCK_CLOSED = {"open": False, "phase": "closed"}

CHAIN = {
    "underlying": "SPY",
    "expiry": "2026-10-16",
    "dte": 45,
    "calls": [
        {"option_symbol": "SPY261016C00510000", "strike": 510.0, "option_type": "call",
         "bid": 2.10, "ask": 2.30, "mid": 2.20, "spread_pct": 0.09, "open_interest": 4200,
         "volume": 350, "iv": 0.22, "delta": 0.16, "gamma": 0.012, "theta": -0.08, "vega": 0.35},
        {"option_symbol": "SPY261016C00530000", "strike": 530.0, "option_type": "call",
         "bid": 0.95, "ask": 1.05, "mid": 1.00, "spread_pct": 0.10, "open_interest": 3100,
         "volume": 210, "iv": 0.21, "delta": 0.08, "gamma": 0.008, "theta": -0.05, "vega": 0.22},
    ],
    "puts": [
        {"option_symbol": "SPY261016P00450000", "strike": 450.0, "option_type": "put",
         "bid": 2.05, "ask": 2.25, "mid": 2.15, "spread_pct": 0.09, "open_interest": 5100,
         "volume": 400, "iv": 0.23, "delta": -0.16, "gamma": 0.012, "theta": -0.08, "vega": 0.35},
        {"option_symbol": "SPY261016P00430000", "strike": 430.0, "option_type": "put",
         "bid": 0.90, "ask": 1.00, "mid": 0.95, "spread_pct": 0.10, "open_interest": 3800,
         "volume": 180, "iv": 0.22, "delta": -0.08, "gamma": 0.008, "theta": -0.05, "vega": 0.22},
    ],
}

NEWS = [
    {"id": "n1", "headline": "Fed signals steady path; equities grind higher",
     "source": "Reuters", "url": "https://example.com/1", "symbols": ["SPY", "QQQ"],
     "summary": "Rate-cut odds firm after dovish remarks.", "ts": "2026-09-01T14:00:00Z"},
    {"id": "n2", "headline": "Retail chatter turns bullish on broad ETFs",
     "source": "SeekingAlpha", "url": "https://example.com/2", "symbols": ["SPY"],
     "summary": "Social sentiment flips positive.", "ts": "2026-09-01T15:30:00Z"},
    {"id": "n3", "headline": "Analysts flag stretched valuations into FOMC",
     "source": "Bloomberg", "url": "https://example.com/3", "symbols": ["SPY", "QQQ"],
     "summary": "Strategists warn of event risk.", "ts": "2026-09-01T16:10:00Z"},
]

SCREENER = [
    {"symbol": "SPY", "price": 505.0, "momentum_pct": 1.4,
     "volume_note": "3σ volume", "optionable": True,
     "reason": "watchlist + elevated volume"},
    {"symbol": "QQQ", "price": 490.0, "momentum_pct": -0.8,
     "volume_note": "mild red", "optionable": True, "reason": "movers"},
    {"symbol": "NVDA", "price": 128.0, "momentum_pct": 2.1,
     "volume_note": "most active", "optionable": True, "reason": "most-actives"},
]

# ---------------------------------------------------------------- LLM responses (recorded)

SENTIMENT_FIXTURE = {
    "symbol": "SPY",
    "public_sentiment": 0.31,
    "confidence": 0.68,
    "source_breakdown": [
        {"source": "Reuters", "credibility": 0.9, "lean": 0.4, "headline": "Fed signals steady path"},
        {"source": "SeekingAlpha", "credibility": 0.4, "lean": -0.2, "note": "social chatter"},
    ],
    "expert_consensus": {"lean": 0.3, "summary": "Analysts cite stable macro but flag FOMC."},
    "event_flags": ["FOMC Wed", "CPI Thu"],
    "citations": ["https://example.com/1", "https://example.com/3"],
}

DEBATE_TORO_R1 = {
    "round": 1, "agent": "toro",
    "claims": [
        {"fact_ref": "trend.mom", "argument": "Momentum is positive with 3σ volume participation — institutions are buying this tape."},
        {"fact_ref": "ivr.value", "argument": "IV rank above floor means premium selling is being paid for."},
        {"fact_ref": "senti.score", "argument": "Public sentiment leans positive and experts confirm stability."},
    ],
    "risks": ["A hot CPI print could whipsaw gamma positions."],
    "conviction": 0.7,
}

DEBATE_URSA_R1 = {
    "round": 1, "agent": "ursa",
    "claims": [
        {"fact_ref": "event.hours", "argument": "FOMC sits inside the blackout window — event risk is live."},
        {"fact_ref": "ivr.value", "argument": "IVR is mid-range; the premium on offer does not pay for event gap risk."},
        {"fact_ref": "senti.flags", "argument": "Senti flagged both FOMC and CPI on the calendar."},
    ],
    "risks": ["Squeeze risk if breakout accelerates through short strikes."],
    "conviction": 0.65,
}

DEBATE_TORO_R2 = {
    "round": 2, "agent": "toro",
    "claims": [{"fact_ref": "event.hours", "argument": "Blackout applies to entries now; we can still stage for post-event premium."}],
    "risks": [],
    "conviction": 0.6,
}

DEBATE_URSA_R2 = {
    "round": 2, "agent": "ursa",
    "claims": [{"fact_ref": "liquidity.spread", "argument": "Spreads are fine — that's not the issue; the calendar is."}],
    "risks": [],
    "conviction": 0.7,
}

VERDICT_FIXTURE = {
    "direction": "NEUTRAL",
    "conviction": 0.62,
    "key_factor": "Event calendar risk outweighs moderate bullish data.",
    "weakest_link": "Toro's staging argument ignores gap-through risk on short strikes.",
    "model": "gpt-4o",
}

STRUCTURER_CONFIRM = {"decision": "confirm", "reason": "Structure matches regime and verdict; terms sane."}

SAGE_POST_MORTEM = {
    "root_cause": "event_risk_underweighted",
    "failed_signal": "event calendar proximity to entry",
    "missed_check": "IV term structure across the event boundary",
    "lesson": "Block premium-selling within 24h of FOMC or CPI when IVR < 25.",
    "param_proposals": [{"param": "event_blackout_hours", "current": 24, "proposed": 36}],
}

NARRATION_FIXTURE = {
    "lines": [
        "Senti read 3 articles. Two lean bullish, one cautious.",
        "Ursa wasn't convinced — the calendar scared him.",
        "Sgt. Gate said yes. XQ stamped it.",
    ]
}
