"""Alpaca layer tests — paper guards, coids, executor conventions, reconcile."""
from __future__ import annotations

import asyncio

import pytest

import stonks.config as config
from stonks.alpaca.cli import AlpacaCLI, CLIError
from stonks.alpaca.client import AlpacaClient
from stonks.alpaca.executor import (
    ExecutionHalt,
    Executor,
    SurfaceError,
    build_payload,
    make_coid,
)
from stonks.alpaca.mcp import MCPServer
from stonks.alpaca.reconcile import reconcile
from stonks.schemas import Leg, StructureSpec, utcnow


def make_spec(**over) -> StructureSpec:
    legs = [
        Leg(option_symbol="X1", side="sell", ratio=1, strike=510.0, option_type="call"),
        Leg(option_symbol="X2", side="buy", ratio=1, strike=530.0, option_type="call"),
    ]
    base = dict(
        kind="bull_put_spread", intent="bps", symbol="SPY", legs=legs,
        expiry="2026-10-16", dte=40, width=20.0, credit=1.5,
        max_loss=18.5, contracts=2, premium_risk=3700.0,
    )
    base.update(over)
    return StructureSpec(**base)


class TestPaperGuard:
    def test_refuses_live_mode(self, monkeypatch):
        monkeypatch.setattr(config.ENV, "alpaca_mode", "live")
        with pytest.raises(RuntimeError):
            AlpacaClient(test_mode=False)

    def test_test_mode_never_network(self):
        c = AlpacaClient(test_mode=True)
        assert c.test_mode is True
        acc = asyncio.run(c.account())
        assert acc.account_number == "PA-TEST-0001"
        assert acc.equity == 100000.0


class TestCoid:
    def test_format(self):
        ts = utcnow()
        coid = make_coid("ic", "SPY", ts)
        assert coid.startswith("stonks-ic-SPY-")
        assert coid.endswith(ts.strftime("%Y%m%dT%H%M%SZ"))

    def test_deterministic_same_second(self):
        ts = utcnow()
        assert make_coid("ic", "SPY", ts) == make_coid("ic", "SPY", ts)


class TestTestModeData:
    def test_chain_synthetic_black_scholes(self):
        c = AlpacaClient(test_mode=True)
        chain = asyncio.run(c.option_chain("SPY"))
        assert len(chain) >= 100
        atm = [e for e in chain if abs(e.strike - 505.0) < 1.0 and e.option_type == "call"]
        assert atm, "no ATM calls"
        assert 0.3 < (atm[0].delta or 0) < 0.7

    def test_news_and_screener_fixtures(self):
        c = AlpacaClient(test_mode=True)
        news = asyncio.run(c.news("SPY"))
        assert len(news) == 3 and news[0].source == "Reuters"
        screen = asyncio.run(c.screener(5))
        assert {s.symbol for s in screen} >= {"SPY", "QQQ", "NVDA"}

    def test_prices(self):
        c = AlpacaClient(test_mode=True)
        assert asyncio.run(c.snapshot_prices(["SPY"]))["SPY"] == 505.0

    def test_clock_open(self):
        c = AlpacaClient(test_mode=True)
        assert asyncio.run(c.clock()).open is True


class TestExecutor:
    def test_negative_credit_limit_convention(self):
        payload = build_payload(make_spec(), "stonks-bps-SPY-TEST")
        assert payload["limit_price"] == -1.5
        assert payload["order_class"] == "multi_leg"
        assert len(payload["legs"]) == 2

    def test_csp_simple_order(self):
        spec = make_spec(
            kind="csp", intent="csp",
            legs=[Leg(option_symbol="P1", side="sell", ratio=1, strike=450.0, option_type="put")],
        )
        payload = build_payload(spec, "c")
        assert payload["order_class"] == "simple" and payload["side"] == "sell"
        assert payload["limit_price"] < 0

    def test_place_fills_in_test_mode(self):
        ex = Executor(test_mode=True)
        r = asyncio.run(ex.place(make_spec(), "stonks-bps-SPY-TEST"))
        assert r.status == "filled" and r.filled_avg_price == 1.5
        assert r.surface == "api"

    def test_duplicate_coid_raises(self):
        ex = Executor(test_mode=True)
        asyncio.run(ex.place(make_spec(), "stonks-dup"))
        with pytest.raises((SurfaceError, ExecutionHalt)):
            asyncio.run(ex.place(make_spec(), "stonks-dup"))

    def test_close_position(self):
        ex = Executor(test_mode=True)
        r = asyncio.run(ex.close_position(make_spec()))
        assert r.status == "filled"
        assert r.coid.startswith("stonks-close-bps-SPY")

    def test_dry_run_ok(self):
        ex = Executor(test_mode=True)
        assert asyncio.run(ex.dry_run(make_spec(), "c")) is True


class TestCLI:
    def test_fallback_positions(self):
        cli = AlpacaCLI(test_mode=True)
        assert asyncio.run(cli.positions()) == []

    def test_dry_run_local_validation(self):
        cli = AlpacaCLI(test_mode=True)
        ok = asyncio.run(cli.dry_run_order(make_spec()))
        assert ok["ok"] is True and ok["validated"] == "local"

    def test_dry_run_rejects_bad_payload(self):
        cli = AlpacaCLI(test_mode=True)
        bad = make_spec(credit=-1)
        with pytest.raises(CLIError):
            asyncio.run(cli.dry_run_order(bad))


class TestMCP:
    def test_test_mode_unavailable(self):
        server = MCPServer(test_mode=True)
        assert server.available is False
        with pytest.raises(SurfaceError):
            asyncio.run(server.place_option_order(make_spec(), "c"))


class TestReconcile:
    def test_match_in_test_mode(self):
        result = asyncio.run(reconcile(AlpacaClient(test_mode=True), AlpacaCLI(test_mode=True)))
        assert result["match"] is True

    def test_mismatch_detected(self):
        cli = AlpacaCLI(test_mode=True)
        cli._fallback_positions = [{"symbol": "X1", "qty": 2.0}]
        result = asyncio.run(reconcile(AlpacaClient(test_mode=True), cli))
        assert result["match"] is False
        assert result["cli"] == {"X1": 2.0}
