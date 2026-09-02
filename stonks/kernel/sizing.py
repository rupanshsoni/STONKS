"""Position sizing math (RISK.md §4) — code-only, LLMs never see the formula."""
from __future__ import annotations

import math

from stonks.config import RISK
from stonks.schemas import OptionChainEntry


def size_structure(
    kind: str,
    symbol: str,
    chain: list[OptionChainEntry],
    credit: float,
    width: float,
    nav: float,
    strike: float | None = None,
) -> int:
    risk_budget = RISK.max_position_size_pct * nav
    if kind == "csp":
        max_loss_per_unit = (strike - credit) if strike is not None else width
    else:
        max_loss_per_unit = width - credit
    if max_loss_per_unit <= 0:
        return 0
    contracts = math.floor(risk_budget / (max_loss_per_unit * 100.0))
    if contracts < 1:
        # A single contract within the risk budget is the floor: one defined-risk
        # structure whose premium_risk the POSITION_SIZE gate will re-verify.
        contracts = 1 if max_loss_per_unit * 100.0 <= risk_budget * 1.5 else 0
    return contracts
