"""Deterministic structurer (AGENTS.md §6) — code picks every strike, wing, DTE, size.

The LLM confirm step can only confirm or pass; it can never alter terms.
"""
from __future__ import annotations

import math
from datetime import timedelta

from stonks.config import RISK
from stonks.kernel.sizing import size_structure
from stonks.schemas import (
    Lesson,
    OptionChainEntry,
    Regime,
    StructureSpec,
    Leg,
    Verdict,
    utcnow,
)


def _dte_of(entry: OptionChainEntry, today) -> int:
    try:
        expiry = entry.expiry
        if isinstance(expiry, str):
            y, m, d = (int(x) for x in expiry.split("-"))
            from datetime import date
            exp = date(y, m, d)
        else:
            exp = expiry
        return (exp - today).days
    except Exception:
        return 999


def _mid(entry: OptionChainEntry) -> float | None:
    if entry.mid is not None:
        return entry.mid
    if entry.bid is not None and entry.ask is not None and entry.bid > 0:
        return (entry.bid + entry.ask) / 2.0
    return None


def _liquid(entry: OptionChainEntry) -> bool:
    if entry.open_interest is not None:
        return entry.open_interest >= RISK.min_oi
    return entry.volume is not None and entry.volume >= 100


def _pick_leg(
    chain: list[OptionChainEntry],
    option_type: str,
    target_delta: float,
    today,
    require_liquid: bool = True,
) -> OptionChainEntry | None:
    pool = [
        e for e in chain
        if e.option_type == option_type
        and e.delta is not None
        and RISK.target_dte_min <= _dte_of(e, today) <= RISK.target_dte_max
        and (not require_liquid or _liquid(e))
    ]
    if not pool:
        return None
    def distance(e: OptionChainEntry) -> float:
        return abs(abs(e.delta) - target_delta)
    for tolerance in (0.03, 0.06):
        cand = [e for e in pool if distance(e) <= tolerance]
        if cand:
            return min(cand, key=distance)
    return None


def _wing_candidates(
    chain: list[OptionChainEntry],
    option_type: str,
    short: OptionChainEntry,
    target_delta: float,
    today,
) -> list[OptionChainEntry]:
    """Wing candidates beyond the short strike, doctrinal order (nearest to
    target delta first) — the budget filter walks this list tighter if needed."""
    pool = [
        e for e in chain
        if e.option_type == option_type
        and e.delta is not None
        and RISK.target_dte_min <= _dte_of(e, today) <= RISK.target_dte_max
        and _liquid(e)
    ]
    if option_type == "put":
        pool = [e for e in pool if e.strike < short.strike]
    else:
        pool = [e for e in pool if e.strike > short.strike]
    pool.sort(key=lambda e: abs(abs(e.delta) - target_delta))
    # must satisfy the minimum wing width
    return [e for e in pool if abs(short.strike - e.strike) >= RISK.min_wing_width]


def _pick_wing(
    chain: list[OptionChainEntry],
    option_type: str,
    short: OptionChainEntry,
    target_delta: float,
    today,
    nav: float,
) -> OptionChainEntry | None:
    """Budget-aware wing for a TWO-LEG credit spread.

    Doctrine: the 0.08Δ wing is preferred; the POSITION_SIZE budget is the
    hard constraint. Walk from the doctrinal wing toward the short strike and
    take the first whose ACTUAL max-loss (width − net credit) fits at 1 lot.
    """
    budget = RISK.max_position_size_pct * nav
    for wing in _wing_candidates(chain, option_type, short, target_delta, today):
        width = abs(short.strike - wing.strike)
        credit = (_mid(short) or 0.0) - (_mid(wing) or 0.0)
        max_loss = width - credit
        if max_loss > 0 and max_loss * 100.0 <= budget:
            return wing
    return None


def _pick_condor_wings(
    chain: list[OptionChainEntry],
    short_call: OptionChainEntry,
    short_put: OptionChainEntry,
    target_delta: float,
    today,
    nav: float,
) -> tuple[OptionChainEntry, OptionChainEntry] | None:
    """Budget-aware wing PAIR for the iron condor.

    The condor's max loss is max(call_width, put_width) − total net credit —
    both wings' premiums feed the credit, so wings must be chosen jointly.
    Try the doctrinal (0.08Δ) pair first; then tighten each side toward its
    short strike until the whole structure fits the size budget.
    """
    budget = RISK.max_position_size_pct * nav
    call_wings = _wing_candidates(chain, "call", short_call, target_delta, today)
    put_wings = _wing_candidates(chain, "put", short_put, target_delta, today)
    if not call_wings or not put_wings:
        return None
    sc_mid, sp_mid = _mid(short_call) or 0.0, _mid(short_put) or 0.0

    def fits(wc: OptionChainEntry, wp: OptionChainEntry) -> bool:
        credit = (sc_mid + sp_mid) - (_mid(wc) or 0.0) - (_mid(wp) or 0.0)
        width = max(wc.strike - short_call.strike, short_put.strike - wp.strike)
        max_loss = width - credit
        return max_loss > 0 and max_loss * 100.0 <= budget

    # doctrinal pair first
    if fits(call_wings[0], put_wings[0]):
        return call_wings[0], put_wings[0]
    # joint walk: tighten the wider side step by step (each list is sorted
    # doctrinal→tighter; index i,j; advance the side that is wider)
    i = j = 0
    for _ in range(len(call_wings) + len(put_wings)):
        if i >= len(call_wings) or j >= len(put_wings):
            return None
        wc, wp = call_wings[i], put_wings[j]
        if fits(wc, wp):
            return wc, wp
        if (wc.strike - short_call.strike) >= (short_put.strike - wp.strike):
            i += 1
        else:
            j += 1
    return None


def _spread_legs(short: OptionChainEntry, wing: OptionChainEntry) -> tuple[Leg, Leg]:
    return (
        Leg(option_symbol=short.option_symbol, side="sell", ratio=1,
            strike=short.strike, option_type=short.option_type),
        Leg(option_symbol=wing.option_symbol, side="buy", ratio=1,
            strike=wing.strike, option_type=wing.option_type),
    )


def _lesson_blocks(lessons: list[Lesson] | None, symbol: str, iv_rank: float | None) -> bool:
    if not lessons:
        return False
    low_iv = iv_rank is not None and iv_rank < 25
    for lesson in lessons:
        text = lesson.text.lower()
        relevant = (
            symbol.lower() in text
            or "premium-selling" in text
            or "condor" in text
        )
        if relevant and low_iv:
            return True
    return False


def _fits_size_gate(premium_risk: float, nav: float) -> bool:
    """Sizing and the POSITION_SIZE gate must agree: never propose a
    structure the gate must reject (the sizing floor exists for tiny
    accounts; on the desk's NAV it would only generate noise rejections)."""
    return premium_risk <= RISK.max_position_size_pct * nav


def pick_structure(
    verdict: Verdict,
    regime: Regime,
    symbol: str,
    chain: list[OptionChainEntry],
    price: float,
    nav: float,
    lessons: list[Lesson] | None = None,
) -> StructureSpec | None:
    if regime.band == "stressed":
        return None
    if _lesson_blocks(lessons, symbol, regime.iv_rank):
        return None

    today = utcnow().date()
    dte_ref = RISK.target_dte_max
    expiry = None
    for e in chain:
        d = _dte_of(e, today)
        if RISK.target_dte_min <= d <= RISK.target_dte_max:
            expiry = e.expiry
            dte_ref = d
            break

    if regime.band == "choppy":
        if verdict.direction != "BEARISH":
            short_put = _pick_leg(chain, "put", RISK.delta_short, today)
            if short_put is None:
                return None
            credit = _mid(short_put) or 0.0
            if credit <= 0:
                return None
            width = short_put.strike
            contracts = size_structure(
                "csp", symbol, chain, credit, width, nav, strike=short_put.strike
            )
            if contracts < 1:
                return None
            max_loss = short_put.strike - credit
            if not _fits_size_gate(max_loss * contracts * 100.0, nav):
                return None
            return StructureSpec(
                kind="csp", intent="csp", symbol=symbol,
                legs=[Leg(option_symbol=short_put.option_symbol, side="sell", ratio=1,
                          strike=short_put.strike, option_type="put")],
                expiry=expiry or short_put.expiry, dte=dte_ref,
                width=width, credit=round(credit, 2), max_loss=round(max_loss, 2),
                contracts=contracts, premium_risk=round(max_loss * contracts * 100, 2),
                pop=round(1 - abs(short_put.delta or 0.16), 3),
                notes="choppy regime: wheel CSP only",
            )
        return None

    if verdict.direction == "BULLISH":
        short_put = _pick_leg(chain, "put", RISK.delta_short, today)
        if short_put is None:
            return None
        wing_put = _pick_wing(chain, "put", short_put, RISK.delta_wing, today, nav)
        if wing_put is None:
            return None
        credit = (_mid(short_put) or 0.0) - (_mid(wing_put) or 0.0)
        width = short_put.strike - wing_put.strike
        contracts = size_structure("bull_put_spread", symbol, chain, credit, width, nav)
        if credit <= 0 or contracts < 1:
            return None
        legs = [_spread_legs(short_put, wing_put)[0], _spread_legs(short_put, wing_put)[1]]
        max_loss = width - credit
        if not _fits_size_gate(max_loss * contracts * 100.0, nav):
            return None
        return StructureSpec(
            kind="bull_put_spread", intent="bps", symbol=symbol, legs=legs,
            expiry=expiry or short_put.expiry, dte=dte_ref, width=width,
            credit=round(credit, 2), max_loss=round(max_loss, 2), contracts=contracts,
            premium_risk=round(max_loss * contracts * 100, 2),
            pop=round(1 - abs(short_put.delta or 0.16), 3),
            notes="calm regime + bullish verdict",
        )

    if verdict.direction == "BEARISH":
        short_call = _pick_leg(chain, "call", RISK.delta_short, today)
        if short_call is None:
            return None
        wing_call = _pick_wing(chain, "call", short_call, RISK.delta_wing, today, nav)
        if wing_call is None:
            return None
        credit = (_mid(short_call) or 0.0) - (_mid(wing_call) or 0.0)
        width = wing_call.strike - short_call.strike
        contracts = size_structure("bear_call_spread", symbol, chain, credit, width, nav)
        if credit <= 0 or contracts < 1:
            return None
        legs = [_spread_legs(short_call, wing_call)[0], _spread_legs(short_call, wing_call)[1]]
        max_loss = width - credit
        if not _fits_size_gate(max_loss * contracts * 100.0, nav):
            return None
        return StructureSpec(
            kind="bear_call_spread", intent="bcs", symbol=symbol, legs=legs,
            expiry=expiry or short_call.expiry, dte=dte_ref, width=width,
            credit=round(credit, 2), max_loss=round(max_loss, 2), contracts=contracts,
            premium_risk=round(max_loss * contracts * 100, 2),
            pop=round(1 - abs(short_call.delta or 0.16), 3),
            notes="calm regime + bearish verdict",
        )

    short_call = _pick_leg(chain, "call", RISK.delta_short, today)
    short_put = _pick_leg(chain, "put", RISK.delta_short, today)
    if short_call is None or short_put is None:
        return None
    wings = _pick_condor_wings(chain, short_call, short_put, RISK.delta_wing,
                               today, nav)
    if wings is None:
        return None
    wing_call, wing_put = wings
    credit = (
        (_mid(short_call) or 0.0) + (_mid(short_put) or 0.0)
        - (_mid(wing_call) or 0.0) - (_mid(wing_put) or 0.0)
    )
    call_width = wing_call.strike - short_call.strike
    put_width = short_put.strike - wing_put.strike
    width = max(call_width, put_width)
    contracts = size_structure("iron_condor", symbol, chain, credit, width, nav)
    if credit <= 0 or contracts < 1:
        return None
    legs = [
        _spread_legs(short_call, wing_call)[0],
        _spread_legs(short_call, wing_call)[1],
        _spread_legs(short_put, wing_put)[0],
        _spread_legs(short_put, wing_put)[1],
    ]
    max_loss = width - credit
    avg_iv = _avg_iv([short_call, short_put, wing_call, wing_put])
    dte_val = _dte_of(short_call, today)
    expected_move = price * (avg_iv or 0.22) * math.sqrt(max(dte_val, 1) / 252.0)
    if not _fits_size_gate(max_loss * contracts * 100.0, nav):
        return None
    return StructureSpec(
        kind="iron_condor", intent="ic", symbol=symbol, legs=legs,
        expiry=expiry or short_call.expiry, dte=dte_val, width=width,
        credit=round(credit, 2), max_loss=round(max_loss, 2), contracts=contracts,
        premium_risk=round(max_loss * contracts * 100, 2),
        pop=round(1 - abs(short_call.delta or 0.16) - abs(short_put.delta or 0.16), 3),
        expected_move=round(expected_move, 2),
        notes="calm regime + neutral verdict",
    )


def _avg_iv(entries: list[OptionChainEntry]) -> float | None:
    ivs = [e.iv for e in entries if e.iv is not None]
    return sum(ivs) / len(ivs) if ivs else None
