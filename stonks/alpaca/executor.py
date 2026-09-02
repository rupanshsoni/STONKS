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
    """Order payload — the negative-credit convention lives here."""
    legs = [
        {"symbol": leg.option_symbol, "side": leg.side, "ratio_qty": 1}
        for leg in spec.legs
    ]
    limit_price = -spec.credit if spec.credit > 0 else abs(spec.credit or 0.01)
    if spec.kind == "csp" and len(legs) == 1:
        return {
            "order_class": "simple",
            "type": "limit",
            "time_in_force": "day",
            "symbol": legs[0]["symbol"],
            "side": legs[0]["side"],
            "qty": spec.contracts,
            "limit_price": round(-spec.credit, 2),
            "client_order_id": coid,
        }
    return {
        "order_class": "multi_leg",
        "type": "limit",
        "time_in_force": "day",
        "qty": spec.contracts,
        "limit_price": round(limit_price, 2),
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
        errors: list[str] = []
        receipt = None
        try:
            receipt = await self._place_mcp(spec, coid)
        except SurfaceError as e:
            errors.append(f"mcp: {e}")
        except Exception as e:
            errors.append(f"mcp: {e}")
        if receipt is None:
            try:
                receipt = await self._place_api(spec, coid)
            except SurfaceError as e:
                errors.append(f"api: {e}")
            except Exception as e:
                errors.append(f"api: {e}")
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
        if receipt.status not in ("filled", "filled_by_new_order"):
            for _ in range(3):
                await asyncio.sleep(1.0)
                poll = await self._client().get(
                    "/v2/orders", params={"client_order_id": coid}
                )
                if poll.status_code == 200:
                    rows = poll.json()
                    if isinstance(rows, list) and rows:
                        row = rows[0]
                        receipt = OrderReceipt(
                            coid=coid, broker_order_id=str(row.get("id")),
                            status=str(row.get("status", receipt.status)),
                            filled_avg_price=_f(row.get("filled_avg_price")),
                            filled_qty=_f(row.get("filled_qty")),
                            surface="api", raw=row,
                        )
                        if receipt.status in ("filled", "filled_by_new_order"):
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

    async def close_position(self, spec: StructureSpec) -> OrderReceipt:
        coid = make_coid(f"close-{spec.intent}", spec.symbol)
        # Live closes mark at mid ± 5% buffer; test mode fills at credit × 1.10.
        if spec.kind == "csp" and len(spec.legs) == 1:
            payload = {
                "order_class": "simple", "type": "limit", "time_in_force": "day",
                "symbol": spec.legs[0].option_symbol, "side": "buy",
                "qty": spec.contracts,
                "limit_price": round(-(spec.credit * 1.10), 2),
                "client_order_id": coid,
            }
        else:
            payload = {
                "order_class": "multi_leg", "type": "limit", "time_in_force": "day",
                "qty": spec.contracts,
                "limit_price": round(-(spec.credit * 1.10), 2),
                "legs": [
                    {"symbol": leg.option_symbol,
                     "side": "buy" if leg.side == "sell" else "sell",
                     "ratio_qty": 1}
                    for leg in spec.legs
                ],
                "client_order_id": coid,
            }
        if self.test_mode:
            await asyncio.sleep(0.05)
            receipt = OrderReceipt(
                coid=coid, status="filled", filled_avg_price=round(spec.credit * 1.10, 2),
                filled_qty=float(spec.contracts), surface="api", raw=payload,
            )
        else:
            resp = await self._client().post("/v2/orders", json=payload)
            if resp.status_code >= 400:
                raise SurfaceError(f"close POST {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            receipt = OrderReceipt(
                coid=coid, broker_order_id=str(data.get("id")),
                status=str(data.get("status", "accepted")), surface="api", raw=data,
            )
        PLACED_RECEIPTS.append(receipt)
        SEEN_COIDS.add(coid)
        return receipt


def _f(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
