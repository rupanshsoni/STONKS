"""Regime router — VIX band + GEX sign (AGENTS.md §6 menu rows)."""
from __future__ import annotations

from stonks.config import RISK
from stonks.schemas import Regime


def evaluate_regime(vix: float, gex_sign: int = 1, iv_rank: float | None = None) -> Regime:
    if vix >= RISK.vix_stressed or gex_sign < 0:
        band = "stressed"
    elif vix >= RISK.vix_choppy:
        band = "choppy"
    else:
        band = "calm"
    summary = (
        f"VIX {vix:.1f}, GEX {'negative' if gex_sign < 0 else 'positive'}"
        + (f", IV rank {iv_rank:.0f}" if iv_rank is not None else "")
        + f" -> {band}"
    )
    return Regime(band=band, vix=vix, gex_sign=gex_sign, iv_rank=iv_rank, summary=summary)
