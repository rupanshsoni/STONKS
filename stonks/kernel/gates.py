"""The 12 gates (RISK.md §1) — pure code, evaluated ALWAYS, no short-circuit."""
from __future__ import annotations

from dataclasses import dataclass, field

from stonks.config import RISK
from stonks.schemas import (
    GateResult,
    GateVerdict,
    OptionChainEntry,
    PositionView,
    Regime,
    StructureSpec,
)


@dataclass
class GateContext:
    nav: float
    day_pnl: float
    open_positions: list[PositionView] = field(default_factory=list)
    open_risk: float = 0.0
    chain: list[OptionChainEntry] = field(default_factory=list)
    quotes_age_seconds: float = 0.0
    regime: Regime = field(
        default_factory=lambda: Regime(band="calm", vix=15.0)
    )
    iv_rank: float | None = None
    vix: float = 15.0
    vrp_edge: float | None = None
    event_hours_to_nearest: float | None = None
    coid_exists: bool = False
    dry_run_ok: bool = True


def _chain_mid(entry: OptionChainEntry) -> float | None:
    if entry.mid is not None:
        return entry.mid
    if entry.bid is not None and entry.ask is not None:
        return (entry.bid + entry.ask) / 2.0
    return None


def _avg_leg_iv(spec: StructureSpec, chain: list[OptionChainEntry]) -> float | None:
    by_symbol = {e.option_symbol: e for e in chain}
    ivs = []
    for leg in spec.legs:
        entry = by_symbol.get(leg.option_symbol)
        if entry is not None and entry.iv is not None:
            ivs.append(entry.iv)
    if not ivs:
        all_ivs = [e.iv for e in chain if e.iv is not None]
        if not all_ivs:
            return None
        return sum(all_ivs) / len(all_ivs)
    return sum(ivs) / len(ivs)


def _gate_sanity(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if ctx.quotes_age_seconds > RISK.quote_max_age_seconds:
        return GateResult(
            gate="SANITY", passed=False, reason_code="STALE_DATA",
            detail=f"quotes age {ctx.quotes_age_seconds:.0f}s > {RISK.quote_max_age_seconds}s",
        )
    if not ctx.chain:
        return GateResult(gate="SANITY", passed=False, reason_code="BAD_PRICE", detail="chain empty")
    if any(leg.strike <= 0 for leg in spec.legs):
        return GateResult(gate="SANITY", passed=False, reason_code="BAD_PRICE", detail="non-positive strike")
    return GateResult(gate="SANITY", passed=True, detail="quotes fresh, prices positive")


def _gate_regime(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if ctx.regime.band == "stressed":
        return GateResult(
            gate="REGIME", passed=False, reason_code="REGIME_STRESSED",
            detail=f"regime stressed (VIX {ctx.regime.vix:.1f}, GEX sign {ctx.regime.gex_sign})",
        )
    if ctx.regime.gex_sign < 0:
        return GateResult(gate="REGIME", passed=False, reason_code="GEX_NEGATIVE", detail="negative GEX")
    if ctx.regime.band == "choppy" and spec.kind not in ("csp", "iron_condor"):
        return GateResult(
            gate="REGIME", passed=False, reason_code="REGIME_CHOPPY",
            detail=f"choppy regime only allows csp/iron_condor, got {spec.kind}",
        )
    return GateResult(gate="REGIME", passed=True, detail=f"regime {ctx.regime.band} allows {spec.kind}")


def _gate_vrp_edge(spec: StructureSpec, ctx: GateContext) -> GateResult:
    # Live VRP edge (implied − realized, both annualized) is the primary
    # input when provided by the orchestrator; IV-rank/100 is the fallback
    # proxy (test mode + degraded data).
    if ctx.vrp_edge is not None:
        edge = ctx.vrp_edge
        src = "implied−realized"
    elif ctx.iv_rank is not None:
        edge = ctx.iv_rank / 100.0
        src = "ivr proxy"
    else:
        iv = _avg_leg_iv(spec, ctx.chain)
        if iv is None:
            return GateResult(
                gate="VRP_EDGE", passed=False, reason_code="NO_EDGE",
                detail="no IV available on chain",
            )
        edge = iv
        src = "chain IV"
    if edge >= RISK.vrp_min_edge:
        return GateResult(gate="VRP_EDGE", passed=True,
                          detail=f"edge {edge:.3f} ({src}) >= {RISK.vrp_min_edge}")
    return GateResult(
        gate="VRP_EDGE", passed=False, reason_code="EDGE_BELOW_MIN",
        detail=f"edge {edge:.3f} ({src}) < {RISK.vrp_min_edge}",
    )


def _gate_event_risk(spec: StructureSpec, ctx: GateContext) -> GateResult:
    hours = ctx.event_hours_to_nearest
    if hours is None or hours >= RISK.event_blackout_hours:
        return GateResult(gate="EVENT_RISK", passed=True, detail=f"hours to event {hours}")
    return GateResult(
        gate="EVENT_RISK", passed=False, reason_code="EVENT_BLACKOUT",
        detail=f"event in {hours:.1f}h < blackout {RISK.event_blackout_hours}h",
    )


def _gate_defined_risk(spec: StructureSpec, ctx: GateContext) -> GateResult:
    shorts = [leg for leg in spec.legs if leg.side == "sell"]
    longs = [leg for leg in spec.legs if leg.side == "buy"]
    if spec.kind in ("iron_condor", "bull_put_spread", "bear_call_spread"):
        for leg in shorts:
            wing = [l for l in longs if l.option_type == leg.option_type and l.ratio == leg.ratio]
            if not wing:
                return GateResult(
                    gate="DEFINED_RISK", passed=False, reason_code="NOT_ATOMIC",
                    detail=f"short {leg.option_symbol} has no matching long",
                )
        if spec.max_loss < 0 or abs(spec.max_loss - (spec.width - spec.credit)) > 0.01:
            return GateResult(
                gate="DEFINED_RISK", passed=False, reason_code="UNCAPPED",
                detail=f"max_loss {spec.max_loss} != width-credit {spec.width - spec.credit}",
            )
        return GateResult(gate="DEFINED_RISK", passed=True, detail="atomic, capped")
    if spec.kind == "csp":
        if len(shorts) != 1 or shorts[0].option_type != "put":
            return GateResult(
                gate="DEFINED_RISK", passed=False, reason_code="NOT_ATOMIC",
                detail="csp must be a single sold put",
            )
        strike = shorts[0].strike
        if abs(spec.max_loss - (strike - spec.credit)) > 0.01:
            return GateResult(
                gate="DEFINED_RISK", passed=False, reason_code="UNCAPPED",
                detail=f"max_loss {spec.max_loss} != strike-credit {strike - spec.credit}",
            )
        return GateResult(gate="DEFINED_RISK", passed=True, detail="csp cash-reserved, loss capped at strike")
    return GateResult(gate="DEFINED_RISK", passed=False, reason_code="NOT_ATOMIC", detail=f"unknown kind {spec.kind}")


def _gate_liquidity(spec: StructureSpec, ctx: GateContext) -> GateResult:
    by_symbol = {e.option_symbol: e for e in ctx.chain}
    for leg in spec.legs:
        entry = by_symbol.get(leg.option_symbol)
        if entry is None:
            return GateResult(
                gate="LIQUIDITY", passed=False, reason_code="LOW_OI",
                detail=f"leg {leg.option_symbol} missing from chain",
            )
        if entry.open_interest is None:
            if entry.volume is not None and entry.volume >= 100:
                continue
            return GateResult(
                gate="LIQUIDITY", passed=False, reason_code="LOW_OI",
                detail=f"leg {leg.option_symbol} has no OI and volume < 100",
            )
        if entry.open_interest < RISK.min_oi:
            return GateResult(
                gate="LIQUIDITY", passed=False, reason_code="LOW_OI",
                detail=f"leg {leg.option_symbol} OI {entry.open_interest} < {RISK.min_oi}",
            )
    for leg in spec.legs:
        entry = by_symbol.get(leg.option_symbol)
        if entry is None or entry.spread_pct is None:
            continue
        if entry.spread_pct > RISK.max_spread_pct:
            return GateResult(
                gate="LIQUIDITY", passed=False, reason_code="WIDE_SPREAD",
                detail=f"leg {leg.option_symbol} spread {entry.spread_pct:.2f} > {RISK.max_spread_pct}",
            )
    return GateResult(gate="LIQUIDITY", passed=True, detail="all legs liquid")


def _gate_credit_quality(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if spec.width > 0 and spec.credit >= RISK.min_credit_pct_of_width * spec.width:
        return GateResult(
            gate="CREDIT_QUALITY", passed=True,
            detail=f"credit {spec.credit:.2f} >= {RISK.min_credit_pct_of_width:.0%} of width",
        )
    return GateResult(
        gate="CREDIT_QUALITY", passed=False, reason_code="THIN_CREDIT",
        detail=f"credit {spec.credit:.2f} < {RISK.min_credit_pct_of_width:.0%} of width {spec.width}",
    )


def _gate_position_size(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if spec.premium_risk <= RISK.max_position_size_pct * ctx.nav:
        return GateResult(
            gate="POSITION_SIZE", passed=True,
            detail=f"risk {spec.premium_risk:.2f} <= {RISK.max_position_size_pct:.1%} NAV",
        )
    return GateResult(
        gate="POSITION_SIZE", passed=False, reason_code="SIZE_EXCEEDED",
        detail=f"risk {spec.premium_risk:.2f} > {RISK.max_position_size_pct:.1%} NAV {ctx.nav}",
    )


def _gate_portfolio_risk(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if ctx.open_risk + spec.premium_risk <= RISK.max_portfolio_risk_pct * ctx.nav:
        return GateResult(
            gate="PORTFOLIO_RISK", passed=True,
            detail=f"open+risk {ctx.open_risk + spec.premium_risk:.2f} <= {RISK.max_portfolio_risk_pct:.1%} NAV",
        )
    return GateResult(
        gate="PORTFOLIO_RISK", passed=False, reason_code="BUDGET_EXCEEDED",
        detail=f"open+risk {ctx.open_risk + spec.premium_risk:.2f} > {RISK.max_portfolio_risk_pct:.1%} NAV {ctx.nav}",
    )


def _gate_concentration(spec: StructureSpec, ctx: GateContext) -> GateResult:
    same_symbol = sum(1 for p in ctx.open_positions if p.symbol == spec.symbol)
    if same_symbol < RISK.max_structures_per_underlying:
        return GateResult(
            gate="CONCENTRATION", passed=True,
            detail=f"{same_symbol} open on {spec.symbol} < {RISK.max_structures_per_underlying}",
        )
    return GateResult(
        gate="CONCENTRATION", passed=False, reason_code="CONCENTRATION",
        detail=f"{same_symbol} structures on {spec.symbol} >= {RISK.max_structures_per_underlying}",
    )


def _gate_duplicate(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if ctx.coid_exists:
        return GateResult(
            gate="DUPLICATE", passed=False, reason_code="DUPLICATE_ORDER",
            detail="client_order_id already used",
        )
    if not ctx.dry_run_ok:
        return GateResult(
            gate="DUPLICATE", passed=False, reason_code="PREVIEW_FAIL",
            detail="dry-run preview failed",
        )
    return GateResult(gate="DUPLICATE", passed=True, detail="coid fresh, preview passed")


def _gate_daily_halt(spec: StructureSpec, ctx: GateContext) -> GateResult:
    if ctx.day_pnl > -RISK.daily_halt_pct * ctx.nav:
        return GateResult(
            gate="DAILY_HALT", passed=True,
            detail=f"day pnl {ctx.day_pnl:.2f} above halt line {-RISK.daily_halt_pct * ctx.nav:.2f}",
        )
    return GateResult(
        gate="DAILY_HALT", passed=False, reason_code="DAILY_HALT_TRIPPED",
        detail=f"day pnl {ctx.day_pnl:.2f} <= {-RISK.daily_halt_pct * ctx.nav:.2f}",
    )


_GATE_FUNCS = [
    _gate_sanity,
    _gate_regime,
    _gate_vrp_edge,
    _gate_event_risk,
    _gate_defined_risk,
    _gate_liquidity,
    _gate_credit_quality,
    _gate_position_size,
    _gate_portfolio_risk,
    _gate_concentration,
    _gate_duplicate,
    _gate_daily_halt,
]


async def evaluate_gates(spec: StructureSpec, ctx: GateContext) -> GateVerdict:
    results = [fn(spec, ctx) for fn in _GATE_FUNCS]
    approved = all(r.passed for r in results)
    return GateVerdict(
        approved=approved,
        results=results,
        coid=f"{spec.intent}.{spec.symbol}.{spec.expiry}".replace("-", "")[:60],
        score=sum(1 for r in results if r.passed),
    )


def snapshot_config() -> dict:
    return RISK.snapshot()
