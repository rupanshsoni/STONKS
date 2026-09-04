"""Exit ladder (RISK.md §2) — runs before entries, frees risk budget."""
from __future__ import annotations

from stonks.config import RISK
from stonks.schemas import ExitDecision, OptionChainEntry, PositionView


def _mark(view: PositionView, chain: list[OptionChainEntry]) -> float:
    by_symbol = {e.option_symbol: e for e in chain}
    total = 0.0
    for leg in view.legs:
        entry = by_symbol.get(leg.option_symbol)
        if entry is None:
            return view.current_mark or 0.0
        px = entry.mid
        if px is None and entry.bid is not None and entry.ask is not None:
            px = (entry.bid + entry.ask) / 2.0
        if px is None:
            return view.current_mark or 0.0
        sign = 1.0 if leg.side == "sell" else -1.0
        total += sign * px * 100.0
    return total * max(view.qty, 1.0)


def check_exits(view: PositionView, chain: list[OptionChainEntry]) -> ExitDecision | None:
    mark = _mark(view, chain)
    credit = view.entry_credit * 100.0 * max(view.qty, 1.0)
    pnl = credit - mark

    if view.kind != "csp":
        if credit > 0 and pnl >= RISK.profit_target_pct * credit:
            return ExitDecision(rule="profit_target", detail=f"+{RISK.profit_target_pct:.0%} of credit", pnl_est=pnl)
        if credit > 0 and mark - credit >= RISK.hard_stop_multiple * credit:
            return ExitDecision(rule="hard_stop", detail=f"loss {mark - credit:.2f} >= {RISK.hard_stop_multiple}x credit", pnl_est=pnl)
    else:
        if credit > 0 and mark <= (1.0 - RISK.profit_target_pct) * credit:
            return ExitDecision(rule="profit_target", detail=f"put mark decayed {RISK.profit_target_pct:.0%}", pnl_est=pnl)

    if view.dte <= RISK.time_stop_dte:
        return ExitDecision(
            rule="time_stop",
            detail=f"{view.dte} DTE <= {RISK.time_stop_dte} (wheel rolls at {RISK.wheel_roll_dte})",
            pnl_est=pnl,
        )
    return None
