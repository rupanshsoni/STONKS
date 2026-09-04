"""End-to-end smoke test — full pipeline in STONKS_TEST mode, zero network."""
import asyncio
import os
import sys
from pathlib import Path

os.environ["STONKS_TEST"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main() -> int:
    from stonks import fixtures  # noqa
    from stonks.api import journal, orch, store
    from stonks.config import DB_PATH, CONFIG_HISTORY_PATH, JOURNAL_PATH  # noqa

    summary = await orch.tick()
    print(f"cycle: {summary.cycle_id}")
    print(f"candidates considered: {summary.candidates_considered}")
    print(f"orders placed: {summary.orders_placed}")
    print(f"rejections: {summary.rejections}")

    events = journal.read(200)
    print(f"journal events: {len(events)}")
    types = {}
    for e in events:
        types[e.type] = types.get(e.type, 0) + 1
    print("event types:", types)

    filled = [e for e in events if e.type == "order_filled"]
    gated = [e for e in events if e.type == "gate_verdict"]
    print(f"fills: {len(filled)} | gate verdicts: {len(gated)}")

    ledgers = store.open_positions()
    print(f"open positions: {len(ledgers)}")
    for l in ledgers:
        print(f"  {l.symbol} {l.spec.kind} {l.spec.contracts}x credit {l.spec.credit}")

    second = await orch.tick()
    print(f"second cycle: {second.orders_placed} placed, {second.rejections} rejected")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
