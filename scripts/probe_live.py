"""Live read-only probe — validates keys + every data path before going live.

Zero orders. Run with real keys in .env (STONKS_TEST unset/false):

    python scripts/probe_live.py

Checks: paper guard, account (equity + options level), clock, stock
snapshots, screener, news, option chain (contracts + snapshots hydration),
daily bars, VIX/VRP computation. Prints a PASS/FAIL table and exits 1 on
any hard failure.
"""
from __future__ import annotations

import asyncio
import os
import sys

# Windows consoles default to cp1252 — force UTF-8 before any prints
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# refuse to run in test mode — this script exists to validate LIVE keys
if os.environ.get("STONKS_TEST", "").lower() == "true":
    print("STONKS_TEST=true — unset it; this probe validates LIVE keys.")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stonks.alpaca.client import AlpacaClient  # noqa: E402
from stonks.config import ENV  # noqa: E402


async def main() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    print("STONKS live probe (read-only, no orders)\n")

    print("env:")
    check("ALPACA_MODE=paper", ENV.alpaca_mode == "paper", ENV.alpaca_mode)
    check("alpaca keys present", ENV.has_alpaca)
    check("openrouter glm key present", bool(ENV.openrouter_glm_key))
    check("openrouter minimax key present", bool(ENV.openrouter_minimax_key))
    print()

    client = AlpacaClient(test_mode=False)  # guard() runs here

    print("trading api:")
    try:
        acc = await client.account()
        check("account", True,
              f"{acc.account_number} equity={acc.equity:.2f} "
              f"options_level={acc.options_level}")
        if acc.equity < 90000:
            check("fresh 100k account", False, f"equity {acc.equity:.0f} — expected ~100k")
        else:
            check("fresh 100k account", True)
    except Exception as exc:
        check("account", False, str(exc)[:160])
        print("\naccount fetch failed — check keys; aborting remaining live checks.")
        return 1
    try:
        clock = await client.clock()
        check("clock", True, f"open={clock.open} phase={clock.phase}")
    except Exception as exc:
        check("clock", False, str(exc)[:160])
    print()

    print("market data:")
    try:
        px = await client.snapshot_prices(["SPY", "QQQ"])
        check("stock snapshots", bool(px), f"{px}")
    except Exception as exc:
        check("stock snapshots", False, str(exc)[:160])
    try:
        screen = await client.screener(5)
        syms = [c.symbol for c in screen][:8]
        check("screener", len(screen) > 0, f"{syms}")
    except Exception as exc:
        check("screener", False, str(exc)[:160])
    try:
        news = await client.news("SPY", 5)
        check("news", len(news) > 0, f"{len(news)} articles; first: {news[0].headline[:60] if news else 'none'}")
    except Exception as exc:
        check("news", False, str(exc)[:160])
    print()

    print("options data (the critical path):")
    try:
        chain = await client.option_chain("SPY", 30, 45)
        check("chain contracts", len(chain) > 0, f"{len(chain)} contracts")
        quoted = [e for e in chain if e.bid is not None and e.ask is not None]
        check("snapshots hydrated (bid/ask)", len(quoted) > 0,
              f"{len(quoted)}/{len(chain)} quoted")
        with_delta = [e for e in chain if e.delta is not None]
        check("greeks (delta)", len(with_delta) > 0, f"{len(with_delta)} with delta")
        with_oi = [e for e in chain if e.open_interest is not None]
        check("open interest", len(with_oi) > 0, f"{len(with_oi)} with OI")
        with_iv = [e for e in chain if e.iv is not None]
        check("implied vol", len(with_iv) > 0, f"{len(with_iv)} with IV")
        if quoted:
            sample = quoted[len(quoted) // 2]
            check("sample quote sane",
                  0 < (sample.bid or 0) and (sample.ask or 0) >= (sample.bid or 0),
                  f"{sample.option_symbol} {sample.bid}/{sample.ask} "
                  f"delta={sample.delta} iv={sample.iv}")
        if with_delta:
            near = [e for e in chain if e.delta is not None
                    and abs(abs(e.delta) - 0.16) <= 0.06]
            check("16-delta legs findable", len(near) > 0,
                  f"{len(near)} candidates near 0.16 delta")
    except Exception as exc:
        check("option chain", False, str(exc)[:200])
    print()

    print("regime inputs:")
    try:
        bars = await client.daily_bars("SPY", 21)
        check("daily bars", len(bars) >= 10, f"{len(bars)} bars")
    except Exception as exc:
        check("daily bars", False, str(exc)[:160])
    try:
        from stonks.orchestrator import Orchestrator
        orch = Orchestrator(test_mode=False)
        vix = await orch._market_regime_inputs("SPY")
        check("vix proxy computed", 8 < vix < 80, f"vix={vix:.1f}")
        chain = await client.option_chain("SPY", 30, 45)
        await orch._hydrate_symbol_regime("SPY", chain)
        vrp = (getattr(orch, "_symbol_vrp", {}) or {}).get("SPY")
        check("vrp edge computed", vrp is not None and -0.5 < vrp < 0.5,
              f"vrp={vrp:.3f}" if vrp is not None else "none")
        ivr = orch._iv_rank("SPY")
        check("iv rank computed", 0 <= ivr <= 100, f"ivr={ivr:.0f}")
    except Exception as exc:
        check("regime inputs", False, str(exc)[:160])
    print()

    if failures:
        print(f"RESULT: {len(failures)} failure(s): {failures}")
        return 1
    print("RESULT: all checks passed — the desk is safe to run live.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
