"""Journal — append-only JSONL + SSE fan-out (ARCHITECTURE.md §2.7).

The journal is the audit trail: every cycle, verdict, rejection (with reason
codes), post-mortem and fill is appended and mirrored to SSE subscribers and
the memory store. The UI renders the journal; SSE is just its live tail.
"""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from stonks.config import JOURNAL_PATH, ensure_dirs
from stonks.schemas import JournalEvent, utcnow


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, asyncio.Queue[JournalEvent]] = {}
        self._counter = 0

    def subscribe(self) -> asyncio.Queue[JournalEvent]:
        self._counter += 1
        q: asyncio.Queue[JournalEvent] = asyncio.Queue(maxsize=500)
        self._subs[f"sub-{self._counter}"] = q
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs = {k: v for k, v in self._subs.items() if v is not q}

    def publish(self, event: JournalEvent) -> None:
        for q in list(self._subs.values()):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    pass


class Journal:
    def __init__(self, bus: EventBus | None = None, path=None) -> None:
        self.bus = bus or EventBus()
        self.path = JOURNAL_PATH if path is None else path
        ensure_dirs() if path is None else self.path.parent.mkdir(parents=True, exist_ok=True)
        self._mascot_map: dict[str, dict[str, str]] = {}

    def emit(
        self,
        agent: str,
        type_: str,
        summary: str,
        symbol: str | None = None,
        data: dict[str, Any] | None = None,
        cycle_id: str = "",
        surface: str | None = None,
        model: str | None = None,
        level: str = "info",
        persist: bool = True,
    ) -> JournalEvent:
        event = JournalEvent(
            cycle_id=cycle_id,
            agent=agent,  # type: ignore[arg-type]
            type=type_,
            symbol=symbol,
            summary=summary,
            data=data or {},
            surface=surface,  # type: ignore[arg-type]
            model=model,
            level=level,  # type: ignore[arg-type]
            ts=utcnow(),
        )
        if persist:
            self.append(event)
        self.bus.publish(event)
        return event

    def append(self, event: JournalEvent) -> None:
        line = event.model_dump_json()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read(self, limit: int = 500) -> list[JournalEvent]:
        if not self.path.exists():
            return []
        try:
            lines = self.path.read_text(encoding="utf-8").strip().splitlines()
        except Exception:
            return []
        out = []
        for line in lines[-limit:]:
            try:
                out.append(JournalEvent.model_validate(json.loads(line)))
            except Exception:
                continue
        out.reverse()
        return out
