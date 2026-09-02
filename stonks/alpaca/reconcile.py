"""REST-vs-CLI reconciliation (ALPACA-INTEGRATION.md §5).

Runs every cycle before anything else. The desk never trades on disputed state:
on mismatch the orchestrator halts new entries and alerts.
"""
from __future__ import annotations

from stonks.alpaca.cli import AlpacaCLI
from stonks.alpaca.client import AlpacaClient


async def reconcile(client: AlpacaClient, cli: AlpacaCLI) -> dict:
    rest = await client.positions_map()
    cli_rows = await cli.positions()
    cli_map = {r["symbol"]: r["qty"] for r in cli_rows if r.get("symbol")}
    match = rest == cli_map
    return {"match": match, "rest": rest, "cli": cli_map}
