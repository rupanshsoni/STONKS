"""Executor (XQ) — atomic multi-leg orders, idempotent client_order_ids.

Verified Alpaca conventions (ALPACA-INTEGRATION.md §4): credit structures submit
a NEGATIVE limit_price — the limit acts as a floor on credit received. Debits
use positive limits. Surface routing: MCP first (agent tool surface), API
fallback; every failure is journaled by the orchestrator via PLACED_RECEIPTS.
"""
from __future__ import annotations

import asyncio

import httpx

from stonks.config import ENV
from stonks.schemas import Leg, OrderReceipt, StructureSpec, utcnow


class SurfaceError(RuntimeError):
    pass


class ExecutionHalt(RuntimeError):
    def __init__(self, coid: str, spec: StructureSpec, reason: str) -> None:
        self.coid = coid
        self.spec = spec
        self.reason = reason
        super().__init__(f"execution halted for {coid}: {reason}")


PLACED_RECEIPTS: list[OrderReceipt] = []
SEEN_COIDS: set[str] = set()


def make_coid(intent: str, symbol: str, ts=None) -> str:
    ts = ts or utcnow()
    return f"stonks-{intent}-{symbol}-{ts.strftime('%Y%m%dT%H%M%SZ')}"


def build_payload(spec: StructureSpec, coid: str) -> dict:
    """Order payload — Alpaca-verified conventions (docs/reference/postorder).

    Multi-leg: order_class "mleg" (NOT "multi_leg"), qty = strategy units,
    legs carry symbol/side/ratio_qty, and a NEGATIVE limit_price is a credit
    floor (positive = debit). Single-leg sells (CSP) use a POSITIVE limit —
    the negative-credit notation is mleg-only. Prices/qty are strings per spec.
    """
    def _s(v) -> str:
        return f"{v:g}" if isinstance(v, float) else str(v)

    legs = [
        {"symbol": leg.option_symbol, "side": leg.side, "ratio_qty": "1"}
        for leg in spec.legs
    ]
    if spec.kind == "csp" and len(legs) == 1:
        return {
            "order_class": "simple",
            "type": "limit",
            "time_in_force": "day",
            "symbol": legs[0]["symbol"],
            "side": "sell",
            "position_intent": "sell_to_open",
            "qty": _s(spec.contracts),
            "limit_price": _s(round(spec.credit, 2)),
            "client_order_id": coid,
        }
    return {
        "order_class": "mleg",
        "type": "limit",
        "time_in_force": "day",
        "qty": _s(spec.contracts),
        "limit_price": _s(round(-spec.credit, 2)),
        "legs": legs,
        "client_order_id": coid,
    }


class Executor:
    def __init__(self, test_mode: bool = False, http: httpx.AsyncClient | None = None) -> None:
        self.test_mode = test_mode
        self._http = http

    def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url="https://paper-api.alpaca.markets",
                headers={
                    "APCA-API-KEY-ID": ENV.alpaca_key,
                    "APCA-API-SECRET-KEY": ENV.alpaca_secret,
                },
                timeout=30.0,
            )
        return self._http

    async def place(self, spec: StructureSpec, coid: str) -> OrderReceipt:
        if coid in SEEN_COIDS:
            raise SurfaceError(f"duplicate coid {coid} — already executed")
        # API-first routing: the MCP surface is a pinned subprocess whose
        # current PyPI release (2.x) is a complete rewrite with a different
        # tool schema; route REST first for reliability, MCP stays optional.
        errors: list[str] = []
        receipt = None
        try:
            receipt = await self._place_api(spec, coid)
        except SurfaceError as e:
            errors.append(f"api: {e}")
        except Exception as e:
            errors.append(f"api: {e}")
        if receipt is None:
            try:
                receipt = await self._place_mcp(spec, coid)
            except SurfaceError as e:
                errors.append(f"mcp: {e}")
            except Exception as e:
                errors.append(f"mcp: {e}")
        if receipt is None:
            raise ExecutionHalt(coid, spec, " | ".join(errors))
        PLACED_RECEIPTS.append(receipt)
        SEEN_COIDS.add(coid)
        return receipt

    async def _place_api(self, spec: StructureSpec, coid: str) -> OrderReceipt:
        payload = build_payload(spec, coid)
        if self.test_mode:
            await asyncio.sleep(0.05)
            return OrderReceipt(
                coid=coid, status="filled", filled_avg_price=spec.credit,
                filled_qty=float(spec.contracts), surface="api", raw=payload,
            )
        resp = await self._client().post("/v2/orders", json=payload)
        if resp.status_code >= 400:
            raise SurfaceError(f"POST /v2/orders {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        receipt = OrderReceipt(
            coid=coid, broker_order_id=str(data.get("id")),
            status=str(data.get("status", "accepted")), surface="api", raw=data,
        )
        if receipt.status not in ("filled", "filled_by_new_order", "canceled",
                                  "expired", "rejected"):
            for _ in range(6):
                await asyncio.sleep(2.5)
                poll = await self._client().get(
                    "/v2/orders:by_client_order_id", params={"client_order_id": coid}
                )
                if poll.status_code == 200:
                    row = poll.json()
                    if isinstance(row, dict) and row.get("id"):
                        receipt = OrderReceipt(
                            coid=coid, broker_order_id=str(row.get("id")),
                            status=str(row.get("status", receipt.status)),
                            filled_avg_price=_f(row.get("filled_avg_price")),
                            filled_qty=_f(row.get("filled_qty")),
                            surface="api", raw=row,
                        )
                        if receipt.status in ("filled", "filled_by_new_order",
                                              "canceled", "expired", "rejected"):
                            break
        return receipt

    async def _place_mcp(self, spec: StructureSpec, coid: str) -> OrderReceipt:
        from stonks.alpaca.mcp import MCPServer
        server = MCPServer(test_mode=self.test_mode)
        result = await server.place_option_order(spec, coid)
        return OrderReceipt(
            coid=coid, status=str(result.get("status", "filled")),
            filled_avg_price=_f(result.get("filled_avg_price", spec.credit)),
            filled_qty=float(result.get("filled_qty", spec.contracts)),
            surface="mcp", raw=result,
        )

    async def dry_run(self, spec: StructureSpec, coid: str) -> bool:
        from stonks.alpaca.cli import AlpacaCLI, CLIError
        try:
            cli = AlpacaCLI(test_mode=self.test_mode)
            result = await cli.dry_run_order(spec)
            return bool(result.get("ok", False))
        except CLIError:
            return False
        except Exception:
            return True

    async def _cancel_open_orders(self, symbols: list[str]) -> int:
        """Cancel all open orders touching these option symbols.

        Verified live: Alpaca rejects an opposite-side close while the entry
        order is still working ("potential wash trade detected. use complex
        orders", 403). The desk's exit ladder always cancels remnants first.
        """
        if self.test_mode:
            return 0
        canceled = 0
        try:
            resp = await self._client().get(
                "/v2/orders", params={"status": "open", "limit": 500}
            )
            if resp.status_code != 200:
                return 0
            for row in resp.json():
                leg_syms = {l.get("symbol") for l in (row.get("legs") or [])}
                if row.get("symbol"):
                    leg_syms.add(row["symbol"])
                if leg_syms & set(symbols):
                    c = await self._client().delete(f"/v2/orders/{row['id']}")
                    if c.status_code in (200, 204):
                        canceled += 1
        except Exception:
            pass
        return canceled

    async def close_position(
        self, spec: StructureSpec, max_debit: float | None = None
    ) -> OrderReceipt:
        """Close a credit structure by buying it back.

        max_debit: per-contract debit limit for the buyback. Priced off the
        CURRENT structure value (see orchestrator) — a static multiple of
        entry credit would never fill a hard-stop (the spread expanded) and
        would leave the losing position open. Fallback cap = width (max
        structural loss; always marketable, bounded by construction).
        """
        coid = make_coid(f"close-{spec.intent}", spec.symbol)
        # Cancel any still-working entry/exit orders on these legs first —
        # an open opposite order makes the close a rejected wash trade.
        leg_syms = [leg.option_symbol for leg in spec.legs]
        await self._cancel_open_orders(leg_syms)
        if max_debit is None:
            max_debit = max(min(spec.width, max(spec.credit * 2.5, 0.05)), 0.05)
        max_debit = round(max(max_debit, 0.05), 2)
        # Close = buy back what was sold (defined-risk structures). For mleg
        # closes, limit_price is the max DEBIT we'll pay — positive. For a
        # single-leg CSP close it's a simple buy with a positive limit.
        def _s(v) -> str:
            return f"{v:g}" if isinstance(v, float) else str(v)

        if spec.kind == "csp" and len(spec.legs) == 1:
            payload = {
                "order_class": "simple", "type": "limit", "time_in_force": "day",
                "symbol": spec.legs[0].option_symbol, "side": "buy",
                "position_intent": "buy_to_close",
                "qty": _s(spec.contracts),
                "limit_price": _s(max_debit),
                "client_order_id": coid,
            }
        else:
            payload = {
                "order_class": "mleg", "type": "limit", "time_in_force": "day",
                "qty": _s(spec.contracts),
                "limit_price": _s(max_debit),
                "legs": [
                    {"symbol": leg.option_symbol,
                     "side": "buy" if leg.side == "sell" else "sell",
                     "ratio_qty": "1"}
                    for leg in spec.legs
                ],
                "client_order_id": coid,
            }
        if self.test_mode:
            await asyncio.sleep(0.05)
            receipt = OrderReceipt(
                coid=coid, status="filled",
                filled_avg_price=max_debit,
                filled_qty=float(spec.contracts), surface="api", raw=payload,
            )
        else:
            resp = await self._client().post("/v2/orders", json=payload)
            if resp.status_code >= 400:
                # already-flat closes are a no-op success, not an error
                txt = resp.text[:200]
                if "position" in txt.lower() and ("does not exist" in txt.lower()
                                                  or "no such" in txt.lower()):
                    receipt = OrderReceipt(
                        coid=coid, status="canceled", surface="api",
                        raw={"note": "already flat"},
                    )
                    PLACED_RECEIPTS.append(receipt)
                    return receipt
                raise SurfaceError(f"close POST {resp.status_code}: {txt}")
            data = resp.json()
            receipt = OrderReceipt(
                coid=coid, broker_order_id=str(data.get("id")),
                status=str(data.get("status", "accepted")), surface="api", raw=data,
            )
            if receipt.status not in ("filled", "filled_by_new_order", "canceled",
                                      "expired", "rejected"):
                for _ in range(6):
                    await asyncio.sleep(2.5)
                    poll = await self._client().get(
                        "/v2/orders:by_client_order_id",
                        params={"client_order_id": coid},
                    )
                    if poll.status_code == 200:
                        row = poll.json()
                        if isinstance(row, dict) and row.get("id"):
                            receipt = OrderReceipt(
                                coid=coid, broker_order_id=str(row.get("id")),
                                status=str(row.get("status", receipt.status)),
                                filled_avg_price=_f(row.get("filled_avg_price")),
                                filled_qty=_f(row.get("filled_qty")),
                                surface="api", raw=row,
                            )
                            if receipt.status in ("filled", "filled_by_new_order",
                                                  "canceled", "expired", "rejected"):
                                break
        PLACED_RECEIPTS.append(receipt)
        SEEN_COIDS.add(coid)
        return receipt


def _f(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
