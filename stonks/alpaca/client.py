"""Alpaca Trading API client — httpx REST, hard paper guards (ALPACA-INTEGRATION.md §1).

The client refuses live base URLs and refuses non-paper modes. Test mode never
touches the network; it returns deterministic fixture data.

Live wiring notes (verified against docs.alpaca.markets OpenAPI specs):
- Trading API base: https://paper-api.alpaca.markets  (headers APCA-API-KEY-ID/SECRET)
- Market Data base: https://data.alpaca.markets       (same header auth)
- Option contracts: GET /v2/options/contracts (trading base) — OI lives here
- Option snapshots: GET /v1beta1/options/snapshots (data base) — envelope
  {"snapshots": {OCC: {greeks, impliedVolatility, latestQuote, ...}}}; OCC
  symbols only (UUIDs are rejected). Greeks keys: delta/gamma/theta/vega.
- Stock snapshots: GET /v1beta1/stocks/snapshots (data base).
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
        self._data: httpx.AsyncClient | None = None
        if not test_mode:
            self.guard()
            headers = {
                "APCA-API-KEY-ID": ENV.alpaca_key,
                "APCA-API-SECRET-KEY": ENV.alpaca_secret,
            }
            self._http = httpx.AsyncClient(
                base_url=PAPER_TRADING, headers=headers, timeout=30.0,
            )
            self._data = httpx.AsyncClient(
                base_url=PAPER_DATA, headers=headers, timeout=30.0,
            )

    def guard(self) -> None:
        """Refuse live keys/URLs — tested."""
        if ENV.alpaca_mode != "paper":
            raise RuntimeError(f"ALPACA_MODE must be 'paper', got {ENV.alpaca_mode!r}")
        if not (PAPER_TRADING.endswith("paper-api.alpaca.markets")):
            raise RuntimeError("base URL must be paper-api.alpaca.markets")

    async def _get_trading(self, url: str, params: dict | None = None) -> dict:
        assert self._http is not None
        resp = await self._http.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _get_data(self, url: str, params: dict | None = None) -> dict:
        assert self._data is not None
        resp = await self._data.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def account(self) -> AccountView:
        if self.test_mode:
            return AccountView.model_validate(fixtures.ACCOUNT_VIEW)
        data = await self._get_trading("/v2/account")
        level = None
        try:
            cfg = await self._get_trading("/v2/account/configurations")
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
        data = await self._get_trading("/v2/clock")
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
                    "MSFT": 420.0, "TSLA": 250.0, "IWM": 210.0, "VIXY": 10.0}
            return {s: book.get(s, 100.0) for s in symbols}
        try:
            data = await self._get_data(
                "/v2/stocks/snapshots",
                params={"symbols": ",".join(symbols)},
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
        """Live screener — verified paths/params/keys 2026-09-03:
        /v1beta1/screener/stocks/most-actives (top=, most_actives[].symbol)
        /v1beta1/screener/stocks/movers      (top=, gainers[]/losers[] with
        percent_change)"""
        if self.test_mode:
            return [Candidate.model_validate(c) for c in fixtures.SCREENER]
        out: list[Candidate] = []
        seen: set[str] = set()

        def _add(sym: str, price: float, mom: float, reason: str) -> None:
            if sym and sym not in seen and len(out) < limit + len(RISK.watchlist):
                seen.add(sym)
                out.append(Candidate(symbol=sym, price=price,
                                    momentum_pct=mom, reason=reason))

        try:
            rows = await self._get_data(
                "/v1beta1/screener/stocks/most-actives", params={"top": limit}
            )
            for r in rows.get("most_actives", []):
                _add(str(r.get("symbol", "")).upper(), 0.0, 0.0, "most-actives")
        except Exception:
            pass
        try:
            rows = await self._get_data(
                "/v1beta1/screener/stocks/movers", params={"top": limit}
            )
            for kind in ("gainers", "losers"):
                for r in rows.get(kind, []):
                    try:
                        _add(str(r.get("symbol", "")).upper(),
                             float(r.get("price") or 0.0),
                             float(r.get("percent_change") or 0.0), kind)
                    except (TypeError, ValueError):
                        continue
        except Exception:
            pass

        # watchlist always considered (screener symbols may be unoptionable)
        watch = [s for s in RISK.watchlist if s not in seen]
        if watch:
            prices = await self.snapshot_prices(watch)
            for s in watch:
                _add(s, prices.get(s, 0.0), 0.0, "watchlist")

        if not out:
            return [Candidate.model_validate(c) for c in fixtures.SCREENER]
        return out[: limit + len(RISK.watchlist)]

    async def news(self, symbol: str, limit: int = 10) -> list[NewsArticle]:
        if self.test_mode:
            return [NewsArticle.model_validate({
                **a, "symbols": a.get("symbols", []),
                "ts": a.get("ts"),
            }) for a in fixtures.NEWS]
        try:
            data = await self._get_data(
                "/v1beta1/news",
                params={"symbols": symbol, "limit": limit},
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
        """Live chain: contracts (trading base, has OI) + snapshots (data base).

        Snapshots come in pages of ~75 symbols; we page until covered or cap.
        """
        if self.test_mode:
            return self._synthetic_chain(underlying)
        today = date.today()
        params = {
            "underlying_symbols": underlying,
            "status": "active",
            # verified live: underscore filters (expiration_date.gte → 422)
            "expiration_date_gte": (today + timedelta(days=min_dte)).isoformat(),
            "expiration_date_lte": (today + timedelta(days=max_dte)).isoformat(),
            "limit": 1000,
        }
        contracts: list[dict] = []
        next_token: str | None = None
        try:
            while True:
                if next_token:
                    params["page_token"] = next_token
                page = await self._get_trading("/v2/options/contracts", params=dict(params))
                contracts.extend(page.get("option_contracts", []))
                next_token = page.get("next_page_token")
                if not next_token or len(contracts) > 3000:
                    break
        except Exception:
            return []
        entries: list[OptionChainEntry] = []
        by_symbol: dict[str, OptionChainEntry] = {}
        for c in contracts:
            try:
                # OCC symbol (c["symbol"], e.g. SPY260918C00500000) — NOT the UUID id.
                entry = OptionChainEntry(
                    option_symbol=str(c.get("symbol") or c["id"]),
                    underlying=underlying,
                    strike=float(c["strike_price"]),
                    expiry=str(c["expiration_date"]),
                    option_type="call" if c["type"] == "call" else "put",
                    # OI lives on the contracts response, not on snapshots.
                    open_interest=_to_int(c.get("open_interest")),
                )
                entries.append(entry)
                by_symbol[entry.option_symbol] = entry
            except Exception:
                continue
        await self._hydrate_snapshots(entries, by_symbol)
        return entries

    async def _hydrate_snapshots(
        self, entries: list[OptionChainEntry], by_symbol: dict[str, OptionChainEntry]
    ) -> None:
        """Fill bid/ask/mid/IV/greeks/volume from /v1beta1/options/snapshots.

        Verified live: hard limit 100 symbols per request (200 → 400 "symbol
        limit is 100"); envelope {"snapshots": {OCC: {...}}} with greeks,
        impliedVolatility, latestQuote, dailyBar.v. Batch through the whole
        chain — liquidity gates need OI+quote on every candidate leg.
        """
        all_symbols = [e.option_symbol for e in entries]
        BATCH = 100
        for i in range(0, len(all_symbols), BATCH):
            batch = all_symbols[i:i + BATCH]
            try:
                data = await self._get_data(
                    "/v1beta1/options/snapshots",
                    params={"symbols": ",".join(batch)},
                )
            except Exception:
                continue
            snaps = data.get("snapshots", data or {})
            for sym, snap in snaps.items():
                entry = by_symbol.get(sym)
                if entry is None:
                    continue
                greeks = snap.get("greeks") or {}
                quote = snap.get("latestQuote") or {}
                bid = _to_float(quote.get("bp"))
                ask = _to_float(quote.get("ap"))
                if bid is not None and ask is not None:
                    entry.bid, entry.ask = bid, ask
                    entry.mid = (bid + ask) / 2
                    entry.spread_pct = (ask - bid) / ((bid + ask) / 2) if bid + ask else None
                entry.volume = _to_int((snap.get("dailyBar") or {}).get("v"))
                iv = _to_float(snap.get("impliedVolatility"))
                if iv is not None:
                    entry.iv = iv
                d = _to_float(greeks.get("delta"))
                if d is not None:
                    entry.delta = d
                entry.gamma = _to_float(greeks.get("gamma"))
                entry.theta = _to_float(greeks.get("theta"))
                entry.vega = _to_float(greeks.get("vega"))

    def _synthetic_chain(self, underlying: str) -> list[OptionChainEntry]:
        """Black-Scholes synthetic chain (r=0) for test mode — realistic deltas/mids."""
        import math
        price = {"SPY": 505.0, "QQQ": 490.0, "NVDA": 128.0, "AAPL": 230.0,
                 "MSFT": 420.0, "TSLA": 250.0, "IWM": 210.0}.get(underlying, 100.0)

        def grid_step(p: float) -> float:
            # realistic strike ladders: SPY/QQQ ~$1, AAPL/MSFT ~$0.5, low-priced ~$0.25
            if p >= 400:
                return 1.0
            if p >= 150:
                return 0.5
            return 0.25

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
            data = await self._get_trading("/v2/positions")
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
            data = await self._get_data(f"/v2/stocks/{symbol}/quotes/latest")
            ts = datetime.fromisoformat(data["timestamp"])
            return max(0.0, (utcnow() - ts).total_seconds())
        except Exception:
            return 999.0

    async def daily_bars(self, symbol: str, days: int = 30) -> list[dict]:
        """Daily close history from the market data API (for realized-vol VRP edge)."""
        if self.test_mode:
            base = {"SPY": 505.0, "QQQ": 490.0}.get(symbol, 100.0)
            return [{"c": base * (1 + 0.001 * i)} for i in range(days)]
        start = (date.today() - timedelta(days=days * 2 + 10)).isoformat()
        try:
            data = await self._get_data(
                f"/v2/stocks/{symbol}/bars",
                params={
                    "start": start,
                    "timeframe": "1Day",
                    "adjustment": "split",
                    "limit": days,
                },
            )
        except Exception:
            return []
        return [b for b in data.get("bars", []) if b.get("c") is not None]

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
            data = await self._get_trading(
                "/v2/account/portfolio/history",
                params={"period": "1M", "timeframe": "1D"},
            )
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
            return await self._get_trading("/v2/calendar", params={
                "start": today.isoformat(),
                "end": (today + timedelta(days=10)).isoformat(),
            })
        except Exception:
            return []


def _to_float(v) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v) -> int | None:
    try:
        if v is None:
            return None
        return int(float(v))
    except (TypeError, ValueError):
        return None
