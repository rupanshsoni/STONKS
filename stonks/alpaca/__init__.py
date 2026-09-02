"""Alpaca surfaces — Trading API (httpx REST), official MCP server, CLI."""
from stonks.alpaca.client import AlpacaClient
from stonks.alpaca.executor import (
    ExecutionHalt,
    Executor,
    SurfaceError,
    make_coid,
)
from stonks.alpaca.cli import AlpacaCLI, CLIError
from stonks.alpaca.mcp import MCPServer
from stonks.alpaca.reconcile import reconcile

__all__ = [
    "AlpacaClient",
    "Executor",
    "ExecutionHalt",
    "SurfaceError",
    "make_coid",
    "AlpacaCLI",
    "CLIError",
    "MCPServer",
    "reconcile",
]
