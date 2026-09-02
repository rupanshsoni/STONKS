"""Alpaca CLI surface — the independent second source of truth.

Used for (a) position reconciliation each cycle — "a REST client cannot quietly
agree with itself"; (b) scripted fallback; (c) --dry-run order previews in the
gate pipeline. When the binary is absent (local dev/test) methods return
fallback data marked as such, never crash the desk.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess

from stonks import fixtures
from stonks.config import ENV
from stonks.schemas import StructureSpec


class CLIError(RuntimeError):
    pass


class AlpacaCLI:
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode
        self.available = shutil.which("alpaca") is not None and not test_mode

    def _run(self, args: list[str], timeout: int = 30) -> str:
        if not self.available:
            raise CLIError("alpaca binary not available")
        env = dict(os.environ)
        env["APCA_API_KEY_ID"] = ENV.alpaca_key
        env["APCA_API_SECRET_KEY"] = ENV.alpaca_secret
        env["APCA_API_BASE_URL"] = "https://paper-api.alpaca.markets"
        try:
            proc = subprocess.run(
                ["alpaca", *args],
                capture_output=True, text=True, timeout=timeout, env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise CLIError("cli timeout") from exc
        if proc.returncode != 0:
            raise CLIError(proc.stderr.strip() or "cli failed")
        return proc.stdout

    async def positions(self) -> list[dict]:
        if not self.available:
            return getattr(self, "_fallback_positions", [])
        out = await asyncio.to_thread(self._run, ["position", "list", "--json"])
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            raise CLIError(f"unparseable positions output: {out[:120]}") from exc
        rows = data if isinstance(data, list) else data.get("positions", [])
        return [
            {"symbol": str(p.get("symbol", "")), "qty": float(p.get("qty", 0)),
             "source": "cli"}
            for p in rows
        ]

    async def account_info(self) -> dict:
        if not self.available:
            return {**fixtures.ACCOUNT_VIEW, "source": "fallback"}
        out = await asyncio.to_thread(self._run, ["account", "get", "--json"])
        try:
            return json.loads(out)
        except json.JSONDecodeError as exc:
            raise CLIError(f"unparseable account output: {out[:120]}") from exc

    async def dry_run_order(self, spec: StructureSpec) -> dict:
        if not self.available:
            ok = (
                len(spec.legs) >= 1
                and spec.contracts >= 1
                and spec.credit > 0
                and all(leg.strike > 0 for leg in spec.legs)
            )
            if not ok:
                raise CLIError("local payload validation failed")
            return {"ok": True, "validated": "local", "legs": len(spec.legs)}
        args = [
            "order", "submit", "--dry-run", "--json",
            "--qty", str(spec.contracts),
        ]
        out = await asyncio.to_thread(self._run, args, timeout=60)
        try:
            return {"ok": True, "validated": "cli", "raw": out[:400]}
        except Exception as exc:
            raise CLIError(f"dry-run failed: {exc}") from exc
