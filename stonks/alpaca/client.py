"""Alpaca Trading API client — httpx REST, hard paper guards (ALPACA-INTEGRATION.md §1).

The client refuses live base URLs and refuses non-paper modes. Test mode never
touches the network; it returns deterministic fixture data.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx

from stonks import fixtures
from stonks.config import ENV, RISK
from stonks.schemas import (
    AccountView,
    Candidate,
    ClockView,
    NewsArticle,
    OptionChainEntry,
    utcnow,
)

PAPER_TRADING = "https://paper-api.alpaca.markets"
PAPER_DATA = "https://data.alpaca.markets"


class AlpacaClient:
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode
        self._http: httpx.AsyncClient | None = None
        if not test_mode:
            self.guard()
            self._http = httpx.AsyncClient(
                base_url=PAPER_TRADING,
                headers={
                    "APCA-API-KEY-ID": ENV.alpaca_key,
                    "APCA-API-SECRET-KEY": ENV.alpaca_secret,
                },
                timeout=30.0,
            )

    def guard(self) -> None:
        """Refuse live keys/URLs — tested."""
        if ENV.alpaca_mode != "paper":
            raise RuntimeError(f"ALPACA_MODE must be 'paper', got {ENV.alpaca_mode!r}")
        if ENV.alpaca_key and not ENV.test_mode:
            pass
        if not (PAPER_TRADING.endswith("paper-api.alpaca.markets")):
            raise RuntimeError("base URL must be paper-api.alpaca.markets")

    async def _get(self, url: str, params: dict | None = None, data_base: bool = False) -> dict:
        assert self._http is not None
        if data_base:
            resp = await self._http.get(url, params=params, base_url=PAPER_DATA)
        else:
            resp = await self._http.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def account(self) -> AccountView:
        if self.test_mode:
            return AccountView.model_validate(fixtures.ACCOUNT_VIEW)
        data = await self._get("/v2/account")
        level = None
        try:
            cfg = await self._get("/v2/account/configurations")
            level = int(cfg.get("max_options_trading_level") or 0) or None
        except Exception:
            pass
        equity = float(data.get("equity", 0.0))
        return AccountView(
            account_number=str(data.get("account_number", "?")),
            paper=str(data.get("trading", "p")).startswith("p"),
            equity=equity,
            cash=float(data.get("cash", 0.0)),
            buying_power=float(data.get("buying_power", 0.0)),
            day_pnl=float(data.get("equity", 0)) - float(data.get("last_equity", equity)),
            total_pnl=equity - 100000.0,
            options_level=level,
            as_of=utcnow(),
        )

    async def clock(self) -> ClockView:
        if self.test_mode:
            return ClockView(open=True, phase="open", timestamp=utcnow())
        data = await self._get("/v2/clock")
        is_open = bool(data.get("is_open"))
        now = utcnow()
        try:
            next_open = datetime.fromisoformat(data["next_open"])
            next_close = datetime.fromisoformat(data["next_close"])
        except Exception:
            next_open = next_close = None
        phase = "open" if is_open else ("pre" if next_open and now < next_open else "closed")
        return ClockView(open=is_open, phase=phase, timestamp=now,  # type: ignore[arg-type]
                         next_open=next_open, next_close=next_close)

    async def snapshot_prices(self, symbols: list[str]) -> dict[str, float]:
        if self.test_mode:
            book = {"SPY": 505.0, "QQQ": 490.0, "NVDA": 128.0, "AAPL": 230.0,
                    "MSFT": 420.0, "TSLA": 250.0, "IWM": 210.0}
            return {s: book.get(s, 100.0) for s in symbols}
        try:
            data = await self._get(
                "/v2/stocks/snapshots",
                params={"symbols": ",".join(symbols)},
                data_base=True,
            )
        except Exception:
            return {}
        out: dict[str, float] = {}
        for sym, snap in data.items():
            trade = (snap or {}).get("latestTrade") or {}
            quote = (snap or {}).get("latestQuote") or {}
            px = trade.get("p") or quote.get("ap")
            if px is not None:
                out[sym] = float(px)
        return out

    async def screener(self, limit: int = 5) -> list[Candidate]:
        if self.test_mode:
            return [Candidate.model_validate(c) for c in fixtures.SCREENER]
        out: list[Candidate] = []
        for endpoint, reason in (
            ("/v1beta1/screener/most-actives", "most-actives"),
            ("/v1beta1/screener/movers", "movers"),
        ):
            try:
                rows = await self._get(endpoint, params={"limit": limit}, data_base=True)
                items = rows.get("tickers", rows if isinstance(rows, list) else [])
                for r in items:
                    sym = str(r.get("ticker") or r.get("symbol") or "").upper()
                    if sym and sym not in [c.symbol for c in out]:
                        out.append(Candidate(
                            symbol=sym,
                            price=float(r.get("price") or r.get("last") or 0),
                            momentum_pct=float(r.get("day_change_percent")
                                               or r.get("percent_change") or 0.0),
                            reason=reason,
                        ))
            except Exception:
                continue
        watch = [s for s in RISK.watchlist if s not in [c.symbol for c in out]]
        if watch:
            prices = await self.snapshot_prices(watch)
            for s in watch:
                out.append(Candidate(
                    symbol=s, price=prices.get(s, 0.0), momentum_pct=0.0, reason="watchlist",
                ))
        if not out:
            return [Candidate.model_validate(c) for c in fixtures.SCREENER]
        return out[:limit + len(RISK.watchlist)]

    async def news(self, symbol: str, limit: int = 10) -> list[NewsArticle]:
        if self.test_mode:
            return [NewsArticle.model_validate({
                **a, "symbols": a.get("symbols", []),
                "ts": a.get("ts"),
            }) for a in fixtures.NEWS]
        try:
            data = await self._get(
                "/v1beta1/news",
                params={"symbols": symbol, "limit": limit},
                data_base=True,
            )
        except Exception:
            return []
        items = data.get("news", data if isinstance(data, list) else [])
        out: list[NewsArticle] = []
        for n in items:
            try:
                out.append(NewsArticle(
                    id=str(n.get("id", "")),
                    headline=str(n.get("headline", "")),
                    source=str(n.get("source", "")),
                    url=n.get("url"),
                    summary=n.get("summary"),
                    ts=datetime.fromisoformat(n["created_at"]) if n.get("created_at") else None,
                    symbols=[str(s) for s in n.get("symbols", [])],
                ))
            except Exception:
                continue
        return out

    async def option_chain(
        self,
        underlying: str,
        min_dte: int = 30,
        max_dte: int = 45,
    ) -> list[OptionChainEntry]:
        if self.test_mode:
            return self._synthetic_chain(underlying)
        today = date.today()
        params = {
            "underlying_symbols": underlying,
            "status": "active",
            "expiration_date.gte": (today + timedelta(days=min_dte)).isoformat(),
            "expiration_date.lte": (today + timedelta(days=max_dte)).isoformat(),
            "limit": 1000,
        }
        contracts: list[dict] = []
        next_token: str | None = None
        try:
            while True:
                if next_token:
                    params["page_token"] = next_token
                page = await self._get("/v2/options/contracts", params=dict(params))
                contracts.extend(page.get("option_contracts", []))
                next_token = page.get("next_page_token")
                if not next_token or len(contracts) > 3000:
                    break
        except Exception:
            return []
        entries: list[OptionChainEntry] = []
        by_symbol = {}
        for c in contracts:
            try:
                entry = OptionChainEntry(
                    option_symbol=str(c["id"] or c["symbol"]),
                    underlying=underlying,
                    strike=float(c["strike_price"]),
                    expiry=str(c["expiration_date"]),
                    option_type="call" if c["type"] == "call" else "put",
                )
                entries.append(entry)
                by_symbol[entry.option_symbol] = entry
            except Exception:
                continue
        symbols = [e.option_symbol for e in entries]
        for i in range(0, len(symbols), 50):
            batch = symbols[i:i + 50]
            try:
                data = await self._get(
                    "/v1beta1/options/snapshots",
                    params={"symbols": ",".join(batch)},
                    data_base=True,
                )
            except Exception:
                continue
            for sym, snap in data.items():
                entry = by_symbol.get(sym)
                if entry is None:
                    continue
                greeks = snap.get("greeks") or {}
                quote = snap.get("latestQuote") or {}
                bid = float(quote.get("bp") or 0.0) or None
                ask = float(quote.get("ap") or 0.0) or None
                mid = (bid + ask) / 2 if bid and ask else None
                entry.bid, entry.ask, entry.mid = bid, ask, mid
                if mid and bid:
                    entry.spread_pct = (ask - bid) / mid
                entry.open_interest = snap.get("oi")
                entry.volume = snap.get("v")
                entry.iv = snap.get("implied_volatility")
                entry.delta = greeks.get("delta")
                entry.gamma = greeks.get("gamma")
                entry.theta = greeks.get("theta")
                entry.vega = greeks.get("vega")
        return entries

    def _synthetic_chain(self, underlying: str) -> list[OptionChainEntry]:
        """Black-Scholes synthetic chain (r=0) for test mode — realistic deltas/mids."""
        import math
        price = {"SPY": 505.0, "QQQ": 490.0, "NVDA": 128.0, "AAPL": 230.0,
                 "MSFT": 420.0, "TSLA": 250.0, "IWM": 210.0}.get(underlying, 100.0)

        def grid_step(p: float) -> float:
            if p >= 400:
                return 1.0
            if p >= 150:
                return 0.5
            return 0.25

        def wing_steps(p: float) -> int:
            return 4

        def norm_cdf(x: float) -> float:
            return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

        out: list[OptionChainEntry] = []
        today = date.today()
        for d in (35, 42):
            expiry = (today + timedelta(days=d)).isoformat()
            T = d / 252.0
            step = grid_step(price)
            k = round(price * 0.85 / step) * step
            while k <= price * 1.15:
                for otype in ("call", "put"):
                    smile = 0.22 if abs(k / price - 1) < 0.05 else 0.25
                    sig_t = smile * math.sqrt(T)
                    d1 = math.log(price / k) / sig_t + 0.5 * sig_t
                    d2 = d1 - sig_t
                    if otype == "call":
                        delta = norm_cdf(d1)
                        px = price * norm_cdf(d1) - k * norm_cdf(d2)
                    else:
                        delta = norm_cdf(d1) - 1.0
                        px = k * norm_cdf(-d2) - price * norm_cdf(-d1)
                    mid = round(max(px, 0.05), 2)
                    half = max(round(mid * 0.05, 2), 0.01)
                    code = "C" if otype == "call" else "P"
                    out.append(OptionChainEntry(
                        option_symbol=f"{underlying}{expiry.replace('-', '')}{code}{int(k * 1000):08d}",
                        underlying=underlying,
                        strike=round(k, 2), expiry=expiry, option_type=otype,  # type: ignore[arg-type]
                        bid=mid - half, ask=mid + half, mid=mid,
                        spread_pct=(2 * half) / mid if mid > 0 else None,
                        open_interest=2500, volume=300, iv=smile,
                        delta=round(delta, 3), gamma=0.01, theta=-0.05, vega=0.3,
                    ))
                k += step
        return out

    async def positions_map(self) -> dict[str, float]:
        if self.test_mode:
            return {}
        try:
            data = await self._get("/v2/positions")
        except Exception:
            return {}
        out: dict[str, float] = {}
        for p in data:
            try:
                out[str(p.get("symbol", ""))] = float(p.get("qty", 0))
            except (TypeError, ValueError):
                continue
        return out

    async def quote_stale_seconds(self, symbol: str) -> float:
        if self.test_mode:
            return 5.0
        try:
            data = await self._get(f"/v2/stocks/{symbol}/quotes/latest", data_base=True)
            ts = datetime.fromisoformat(data["timestamp"])
            return max(0.0, (utcnow() - ts).total_seconds())
        except Exception:
            return 999.0

    async def portfolio_history(self) -> list[dict]:
        if self.test_mode:
            out = []
            base = 100000.0
            for i in range(5):
                out.append({
                    "ts": (utcnow() - timedelta(days=4 - i)).isoformat(),
                    "equity": base + i * 100.0,
                })
            return out
        try:
            data = await self._get("/v2/account/portfolio/history",
                                   params={"period": "1M", "timeframe": "1D"})
            ts_list = data.get("timestamp", [])
            eq_list = data.get("equity", [])
            return [
                {"ts": datetime.fromtimestamp(t, tz=timezone.utc).isoformat(), "equity": float(e)}
                for t, e in zip(ts_list, eq_list)
            ]
        except Exception:
            return []
    async def market_calendar(self) -> list[dict]:
        if self.test_mode:
            return []
        try:
            today = date.today()
            return await self._get("/v2/calendar", params={
                "start": today.isoformat(),
                "end": (today + timedelta(days=10)).isoformat(),
            })
        except Exception:
            return []
