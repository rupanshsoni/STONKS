"""Kernel tests — the 12 gates, regime, sizing, structuring, param bounds."""
from __future__ import annotations

import asyncio
import random
from datetime import date, timedelta

import pytest

from stonks.config import PARAM_BOUNDS, RISK, validate_param_proposal
from stonks.kernel.gates import GateContext, evaluate_gates
from stonks.kernel.regime import evaluate_regime
from stonks.kernel.sizing import size_structure
from stonks.kernel.structuring import pick_structure
from stonks.schemas import (
    Leg,
    OptionChainEntry,
    PositionView,
    Regime,
    StructureSpec,
    Verdict,
)


def make_chain() -> list[OptionChainEntry]:
    out = []
    today = date.today()
    expiry = (today + timedelta(days=40)).isoformat()
    for i, strike in enumerate(range(430, 580, 5)):
        for otype in ("call", "put"):
            mid = 5.0 + (i % 4)
            out.append(OptionChainEntry(
                option_symbol=f"SPY{expiry.replace('-', '')}{'C' if otype == 'call' else 'P'}{strike:08d}",
                underlying="SPY", strike=float(strike), expiry=expiry,
                option_type=otype,  # type: ignore[arg-type]
                bid=mid - 0.2, ask=mid + 0.2, mid=mid, spread_pct=0.08,
                open_interest=3000, volume=250, iv=0.25,
                delta=(0.3 if otype == "call" else -0.3),
                gamma=0.01, theta=-0.05, vega=0.3,
            ))
    return out


def make_spec(**over) -> StructureSpec:
    legs = [
        Leg(option_symbol="SPY_CALL_A", side="sell", ratio=1, strike=510.0, option_type="call"),
        Leg(option_symbol="SPY_CALL_B", side="buy", ratio=1, strike=530.0, option_type="call"),
        Leg(option_symbol="SPY_PUT_A", side="sell", ratio=1, strike=450.0, option_type="put"),
        Leg(option_symbol="SPY_PUT_B", side="buy", ratio=1, strike=430.0, option_type="put"),
    ]
    base = dict(
        kind="iron_condor", intent="ic", symbol="SPY", legs=legs,
        expiry=(date.today() + timedelta(days=40)).isoformat(), dte=40,
        width=20.0, credit=3.0, max_loss=17.0, contracts=5,
        premium_risk=850.0, pop=0.68,
    )
    base.update(over)
    return StructureSpec(**base)


def make_chain_with(spec_legs) -> list[OptionChainEntry]:
    out = []
    today = date.today()
    expiry = (today + timedelta(days=40)).isoformat()
    for leg in spec_legs:
        out.append(OptionChainEntry(
            option_symbol=leg.option_symbol, underlying="SPY",
            strike=leg.strike, expiry=expiry, option_type=leg.option_type,
            bid=2.8, ask=3.2, mid=3.0, spread_pct=0.13,
            open_interest=3000, volume=250, iv=0.25,
            delta=-0.16 if leg.option_type == "put" else 0.16,
            gamma=0.01, theta=-0.05, vega=0.3,
        ))
    return out


def make_ctx(**over) -> GateContext:
    spec_legs = make_spec().legs
    base = dict(
        nav=100000.0, day_pnl=0.0, open_positions=[], open_risk=0.0,
        chain=make_chain_with(spec_legs), quotes_age_seconds=10.0,
        regime=Regime(band="calm", vix=15.0), iv_rank=30.0, vix=15.0,
        event_hours_to_nearest=48.0, coid_exists=False, dry_run_ok=True,
    )
    base.update(over)
    return GateContext(**base)


def first_fail(v):
    return next((r for r in v.results if not r.passed), None)


class TestRegime:
    def test_calm(self):
        assert evaluate_regime(15.0, 1).band == "calm"

    def test_choppy(self):
        assert evaluate_regime(25.0, 1).band == "choppy"

    def test_stressed_vix(self):
        assert evaluate_regime(40.0, 1).band == "stressed"

    def test_stressed_gex(self):
        assert evaluate_regime(15.0, -1).band == "stressed"


class TestGates:
    def test_all_pass(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx()))
        assert v.approved and v.score == 12, [r.detail for r in v.results if not r.passed]

    def test_sanity_stale(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(quotes_age_seconds=999)))
        assert first_fail(v).reason_code == "STALE_DATA"

    def test_sanity_bad_strike(self):
        spec = make_spec(legs=[Leg(option_symbol="X", side="sell", ratio=1, strike=-5.0, option_type="call")])
        v = asyncio.run(evaluate_gates(spec, make_ctx()))
        r = first_fail(v)
        assert r.gate == "SANITY" and r.reason_code == "BAD_PRICE"

    def test_regime_stressed(self):
        v = asyncio.run(evaluate_gates(
            make_spec(), make_ctx(regime=Regime(band="stressed", vix=40.0))))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "REGIME_STRESSED" for r in fails)

    def test_regime_choppy_rejects_directional_spread(self):
        spec = make_spec(kind="bull_put_spread")
        v = asyncio.run(evaluate_gates(
            spec, make_ctx(regime=Regime(band="choppy", vix=22.0))))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "REGIME_CHOPPY" for r in fails)

    def test_regime_choppy_allows_condor(self):
        v = asyncio.run(evaluate_gates(
            make_spec(), make_ctx(regime=Regime(band="choppy", vix=22.0))))
        regime_gate = next(r for r in v.results if r.gate == "REGIME")
        assert regime_gate.passed is True

    def test_vrp_below_min(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(iv_rank=1.0)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "EDGE_BELOW_MIN" for r in fails)

    def test_event_blackout(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(event_hours_to_nearest=10.0)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "EVENT_BLACKOUT" for r in fails)

    def test_defined_risk_not_atomic(self):
        spec = make_spec(legs=[Leg(option_symbol="X1", side="sell", ratio=1, strike=510.0, option_type="call")])
        v = asyncio.run(evaluate_gates(spec, make_ctx()))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "NOT_ATOMIC" for r in fails)

    def test_defined_risk_uncapped(self):
        v = asyncio.run(evaluate_gates(make_spec(max_loss=99.0), make_ctx()))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "UNCAPPED" for r in fails)

    def test_liquidity_low_oi(self):
        chain = make_chain_with(make_spec().legs)
        for e in chain:
            e.open_interest = 10
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(chain=chain)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "LOW_OI" for r in fails)

    def test_liquidity_wide_spread(self):
        chain = make_chain_with(make_spec().legs)
        for e in chain:
            e.spread_pct = 0.9
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(chain=chain)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "WIDE_SPREAD" for r in fails)

    def test_credit_thin(self):
        spec = make_spec(credit=0.1, max_loss=19.9)
        v = asyncio.run(evaluate_gates(spec, make_ctx()))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "THIN_CREDIT" for r in fails)

    def test_position_size(self):
        v = asyncio.run(evaluate_gates(make_spec(premium_risk=50000.0), make_ctx()))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "SIZE_EXCEEDED" for r in fails)

    def test_portfolio_risk(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(open_risk=4900.0)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "BUDGET_EXCEEDED" for r in fails)

    def test_concentration(self):
        pos = [PositionView(
            id=str(i), coid=str(i), symbol="SPY", kind="iron_condor", qty=1,
            entry_ts="2026-09-01T10:00:00Z", entry_credit=1.0, dte=30,
        ) for i in range(2)]
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(open_positions=pos)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "CONCENTRATION" for r in fails)

    def test_duplicate_coid(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(coid_exists=True)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "DUPLICATE_ORDER" for r in fails)

    def test_duplicate_preview_fail(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(dry_run_ok=False)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "PREVIEW_FAIL" for r in fails)

    def test_daily_halt(self):
        v = asyncio.run(evaluate_gates(make_spec(), make_ctx(day_pnl=-3000.0)))
        fails = [r for r in v.results if not r.passed]
        assert any(r.reason_code == "DAILY_HALT_TRIPPED" for r in fails)


class TestPropertyInvariants:
    def test_max_loss_identity_and_sizing(self):
        rng = random.Random(42)
        for _ in range(200):
            width = rng.uniform(1.0, 30.0)
            credit = rng.uniform(0.05, width * 0.4)
            contracts = size_structure("iron_condor", "SPY", [], credit, width, 100000.0)
            max_loss = width - credit
            assert abs(max_loss - (width - credit)) < 1e-9
            if contracts >= 1:
                assert contracts * max_loss * 100 <= 1000.0 * 1.5

    def test_csp_sizing(self):
        # budget $1000; CSP strike 12 credit 2 -> max loss/unit $10*100 = $1000
        assert size_structure("csp", "SPY", [], 2.0, 100.0, 100000.0, strike=12.0) == 1

    def test_csp_sizing_too_risky(self):
        assert size_structure("csp", "SPY", [], 2.0, 100.0, 100000.0, strike=50.0) == 0


class TestParamBounds:
    def test_accept_tighten(self):
        ok, _ = validate_param_proposal("event_blackout_hours", 24, 36)
        assert ok

    def test_reject_loosen(self):
        ok, _ = validate_param_proposal("event_blackout_hours", 36, 24)
        assert not ok

    def test_reject_loosen_size(self):
        ok, _ = validate_param_proposal("max_position_size_pct", 0.005, 0.01)
        assert not ok

    def test_reject_unknown(self):
        ok, _ = validate_param_proposal("max_leverage", 1, 100)
        assert not ok

    def test_reject_out_of_bounds(self):
        ok, _ = validate_param_proposal("event_blackout_hours", 24, 60)
        assert not ok

    def test_bounds_table_covers_sage_params(self):
        for p in ("event_blackout_hours", "min_iv_rank", "max_position_size_pct",
                  "daily_halt_pct", "vix_entry_ceiling"):
            assert p in PARAM_BOUNDS


class TestStructurer:
    def _verdict(self, d):
        return Verdict(direction=d, conviction=0.62, key_factor="t")

    def _bs_chain(self):
        import math
        from stonks.alpaca.client import AlpacaClient
        return AlpacaClient(test_mode=True)._synthetic_chain("SPY")

    def test_calm_neutral_condor(self):
        chain = self._bs_chain()
        reg = evaluate_regime(15.0, 1, 30.0)
        spec = pick_structure(self._verdict("NEUTRAL"), reg, "SPY", chain, 505.0, 100000.0)
        assert spec is not None and spec.kind == "iron_condor"
        assert len(spec.legs) == 4 and spec.credit > 0 and spec.contracts >= 1
        shorts = [l for l in spec.legs if l.side == "sell"]
        longs = [l for l in spec.legs if l.side == "buy"]
        assert len(shorts) == 2 and len(longs) == 2

    def test_stressed_none(self):
        reg = evaluate_regime(40.0, 1, 30.0)
        assert pick_structure(self._verdict("NEUTRAL"), reg, "SPY", self._bs_chain(), 505.0, 100000.0) is None

    def test_choppy_bearish_none(self):
        reg = evaluate_regime(25.0, 1, 30.0)
        assert pick_structure(self._verdict("BEARISH"), reg, "SPY", self._bs_chain(), 505.0, 100000.0) is None
