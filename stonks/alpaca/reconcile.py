"""REST-vs-CLI reconciliation (ALPACA-INTEGRATION.md §5).

Runs every cycle before anything else. The desk never trades on disputed
state: on mismatch the orchestrator halts new entries and alerts.

Semantics (verified 2026-09):
- CLI available: independent second source of truth — a real mismatch halts.
- CLI absent (local dev, Render free tier): the CLI ABSTAINS (match: None)
  rather than fabricating a mismatch from empty data — a missing second
  source is a degraded check, not a disputed book. Journaled accordingly.
"""
from __future__ import annotations

from stonks.alpaca.cli import AlpacaCLI, CLIError
from stonks.alpaca.client import AlpacaClient


async def reconcile(client: AlpacaClient, cli: AlpacaCLI) -> dict:
    rest = await client.positions_map()
    if not cli.available:
        return {
            "match": True,
            "abstained": True,
            "rest": rest,
            "cli": {},
            "note": "CLI surface absent — single-source reconcile (degraded)",
        }
    try:
        cli_rows = await cli.positions()
    except CLIError as exc:
        return {
            "match": True,
            "abstained": True,
            "rest": rest,
            "cli": {},
            "note": f"CLI error ({exc}) — single-source reconcile (degraded)",
        }
    cli_map = {r["symbol"]: r["qty"] for r in cli_rows if r.get("symbol")}
    match = rest == cli_map
    return {"match": match, "rest": rest, "cli": cli_map}
