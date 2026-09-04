"""Official Alpaca MCP server surface — pinned version, supervised subprocess.

The server runs as a uvx stdio subprocess (alpaca-mcp-server==0.3.4 PINNED — a
competitor broke mid-hackathon on an unpinned fastmcp transitive bump; pinning
is the documented lesson). The executor routes here first; on ANY failure the
surface degrades gracefully to the REST API and the mismatch is journaled.
"""
from __future__ import annotations

import asyncio
import json
import os

from stonks.config import ENV
from stonks.schemas import StructureSpec

PINNED_VERSION = "0.3.4"  # historical pin — see start() note before bumping


class MCPServer:
    def __init__(self, test_mode: bool = False) -> None:
        self.test_mode = test_mode
        self.available = False
        self._proc: asyncio.subprocess.Process | None = None
        self._started = False
        self._restarts = 0

    async def start(self) -> bool:
        if self.test_mode:
            self.available = False
            return False
        if self._started and self._proc and self._proc.returncode is None:
            return True
        # NOTE: the executor routes API-first; MCP is the optional agent-tool
        # surface. alpaca-mcp-server 2.x (current PyPI) is a complete rewrite
        # (env vars ALPACA_API_KEY/ALPACA_SECRET_KEY, ALPACA_TOOLSETS, tool
        # schema per github.com/alpacahq/alpaca-mcp-server). The historical
        # 0.3.4 pin below predates that rewrite. If this surface is enabled,
        # install a 1.x pin (last V1 line: alpaca-mcp-server==1.0.13) or port
        # the call site to the V2 place_option_order schema.
        try:
            env = dict(os.environ)
            env["ALPACA_API_KEY"] = ENV.alpaca_key
            env["ALPACA_SECRET_KEY"] = ENV.alpaca_secret
            env["ALPACA_PAPER_TRADE"] = "true"
            self._proc = await asyncio.create_subprocess_exec(
                "uvx", f"alpaca-mcp-server=={PINNED_VERSION}",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                env=env,
            )
        except Exception:
            self.available = False
            return False
        try:
            init = {
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "stonks", "version": "0.1.0"},
                },
            }
            resp = await self._roundtrip(init)
            if resp is None or "error" in resp:
                await self.stop()
                self.available = False
                return False
            note = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            await self._send(note, expect_response=False)
            self.available = True
            self._started = True
            self._restarts = 0
            return True
        except Exception:
            await self.stop()
            self.available = False
            return False

    async def _send(self, message: dict, expect_response: bool = True) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("mcp not started")
        self._proc.stdin.write((json.dumps(message) + "\n").encode())
        await self._proc.stdin.drain()

    async def _read(self, timeout: float = 10.0) -> dict | None:
        if self._proc is None or self._proc.stdout is None:
            return None
        try:
            line = await asyncio.wait_for(self._proc.stdout.readline(), timeout)
        except asyncio.TimeoutError:
            return None
        if not line:
            return None
        text = line.decode(errors="replace").strip()
        if not text:
            return None
        if text.startswith("Content-Length:"):
            while True:
                header = await asyncio.wait_for(self._proc.stdout.readline(), timeout)
                if header in (b"\r\n", b"\n", b""):
                    break
            body = await asyncio.wait_for(self._proc.stdout.readline(), timeout)
            text = body.decode(errors="replace").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def _roundtrip(self, request: dict, timeout: float = 10.0) -> dict | None:
        await self._send(request)
        return await self._read(timeout)

    async def call_tool(self, name: str, arguments: dict, timeout: float = 90.0) -> dict:
        if not self.available:
            await self.start()
        if not self.available:
            from stonks.alpaca.executor import SurfaceError
            raise SurfaceError("mcp unavailable")
        request = {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        resp = await self._roundtrip(request, timeout)
        if resp is None:
            from stonks.alpaca.executor import SurfaceError
            raise SurfaceError(f"mcp tool {name} no response")
        if "error" in resp:
            from stonks.alpaca.executor import SurfaceError
            raise SurfaceError(f"mcp tool {name} error: {resp['error']}")
        result = resp.get("result", {})
        return result if isinstance(result, dict) else {"result": result}

    async def place_option_order(self, spec: StructureSpec, coid: str) -> dict:
        arguments = {
            "legs": [
                {"symbol": leg.option_symbol,
                 "side": leg.side.upper(),
                 "ratio": leg.ratio}
                for leg in spec.legs
            ],
            "quantity": spec.contracts,
            "time_in_force": "day",
            "client_order_id": coid,
            "limit_price": -spec.credit if spec.credit > 0 else abs(spec.credit),
        }
        result = await self.call_tool("place_option_order", arguments)
        return {
            "status": str(result.get("status", "filled")),
            "filled_avg_price": result.get("filled_avg_price", spec.credit),
            "filled_qty": result.get("filled_qty", spec.contracts),
            **result,
        }

    def health(self) -> bool:
        return self.available and self._proc is not None and self._proc.returncode is None

    async def restart(self) -> bool:
        if self._restarts >= 3:
            return False
        self._restarts += 1
        await self.stop()
        self._started = False
        return await self.start()

    async def stop(self) -> None:
        if self._proc is not None:
            try:
                self._proc.kill()
            except ProcessLookupError:
                pass
            self._proc = None
        self.available = False
        self._started = False
