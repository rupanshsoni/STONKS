"""Memory (ARCHITECTURE.md §2.6) — L1 snapshots, L2 ledger, L3 lessons.

All methods synchronous (stdlib sqlite3, WAL, lock-guarded); the orchestrator
calls them via asyncio.to_thread. L3 is the only LLM-written layer and it can
only restrict future behavior.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from stonks.config import DB_PATH, ensure_dirs
from stonks.schemas import (
    AskRequest,
    GateStat,
    JournalEvent,
    Lesson,
    MarketSnapshot,
    PositionLedger,
    utcnow,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS l1_snapshots (ts TEXT PRIMARY KEY, cycle_id TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS l2_positions (coid TEXT PRIMARY KEY, payload TEXT, closed INTEGER DEFAULT 0,
    exit_ts TEXT, exit_pnl REAL, exit_status TEXT);
CREATE TABLE IF NOT EXISTS l3_lessons (id TEXT PRIMARY KEY, created_ts TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, ts TEXT, agent TEXT, type TEXT,
    symbol TEXT, summary TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS asks (id TEXT PRIMARY KEY, payload TEXT);
"""


class MemoryStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._path = Path(db_path) if db_path else DB_PATH
        ensure_dirs()
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self._path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)
        self._db.commit()

    def _exec(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._db.execute(sql, params)
            self._db.commit()
            return cur

    def close(self) -> None:
        self._db.close()

    # ---------------- L1

    def save_snapshot(self, snap: MarketSnapshot) -> None:
        self._exec(
            "INSERT OR REPLACE INTO l1_snapshots VALUES (?,?,?)",
            (snap.ts.isoformat(), snap.cycle_id, snap.model_dump_json()),
        )
        cutoff = (utcnow().timestamp() - 86400)
        with self._lock:
            rows = self._db.execute(
                "SELECT ts FROM l1_snapshots ORDER BY ts DESC"
            ).fetchall()
        stale = [r[0] for r in rows if _iso_age(r[0]) > 86400]
        for ts in stale:
            self._exec("DELETE FROM l1_snapshots WHERE ts=?", (ts,))

    def snapshots_since(self, ts_iso: str) -> list[dict]:
        rows = self._exec(
            "SELECT payload FROM l1_snapshots WHERE ts >= ? ORDER BY ts DESC",
            (ts_iso,),
        ).fetchall()
        return [json.loads(r[0]) for r in rows]

    # ---------------- L2

    def save_position(self, ledger: PositionLedger) -> None:
        self._exec(
            "INSERT OR REPLACE INTO l2_positions (coid, payload, closed, exit_ts, exit_pnl, exit_status) "
            "VALUES (?,?,?,?,?,?)",
            (ledger.coid, ledger.model_dump_json(), 0, None, None, None),
        )

    def open_positions(self) -> list[PositionLedger]:
        rows = self._exec(
            "SELECT payload FROM l2_positions WHERE closed=0 ORDER BY coid"
        ).fetchall()
        return [PositionLedger.model_validate(json.loads(r[0])) for r in rows]

    def get_position(self, coid: str) -> PositionLedger | None:
        rows = self._exec("SELECT payload FROM l2_positions WHERE coid=?", (coid,)).fetchall()
        return PositionLedger.model_validate(json.loads(rows[0][0])) if rows else None

    def mark_closed(self, coid: str, exit_ts, exit_pnl: float, exit_status: str) -> None:
        self._exec(
            "UPDATE l2_positions SET closed=1, exit_ts=?, exit_pnl=?, exit_status=? WHERE coid=?",
            (exit_ts.isoformat() if hasattr(exit_ts, "isoformat") else str(exit_ts),
             float(exit_pnl), exit_status, coid),
        )

    def closed_positions(self) -> list[tuple[PositionLedger, float]]:
        rows = self._exec(
            "SELECT payload, exit_pnl FROM l2_positions WHERE closed=1 ORDER BY exit_ts"
        ).fetchall()
        return [(PositionLedger.model_validate(json.loads(r[0])), r[1]) for r in rows]

    # ---------------- L3

    def save_lesson(self, lesson: Lesson) -> None:
        self._exec(
            "INSERT OR REPLACE INTO l3_lessons VALUES (?,?,?)",
            (lesson.id, lesson.created_ts.isoformat(), lesson.model_dump_json()),
        )
        with self._lock:
            count = self._db.execute("SELECT COUNT(*) FROM l3_lessons").fetchone()[0]
        if count > 50:
            self._exec(
                "DELETE FROM l3_lessons WHERE id IN "
                "(SELECT id FROM l3_lessons ORDER BY created_ts ASC LIMIT ?)",
                (count - 50,),
            )

    def lessons(self, limit: int = 50) -> list[Lesson]:
        rows = self._exec(
            "SELECT payload FROM l3_lessons ORDER BY created_ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [Lesson.model_validate(json.loads(r[0])) for r in rows]

    def record_lesson_applied(self, lesson_id: str, blocked_coid: str) -> None:
        rows = self._exec("SELECT payload FROM l3_lessons WHERE id=?", (lesson_id,)).fetchall()
        if not rows:
            return
        lesson = Lesson.model_validate(json.loads(rows[0][0]))
        lesson.applied_count += 1
        lesson.blocked_trades.append(blocked_coid)
        self._exec(
            "INSERT OR REPLACE INTO l3_lessons VALUES (?,?,?)",
            (lesson.id, lesson.created_ts.isoformat(), lesson.model_dump_json()),
        )

    def relevant_lessons(self, symbol: str, kind: str) -> list[Lesson]:
        all_lessons = self.lessons()
        out = []
        for l in all_lessons:
            text = l.text.lower()
            if (symbol.lower() in text or kind in text) and l not in out:
                out.append(l)
        return out[:5]

    # ---------------- events

    def save_event(self, event: JournalEvent) -> None:
        self._exec(
            "INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?)",
            (event.id, event.ts.isoformat(), event.agent, event.type,
             event.symbol, event.summary, event.model_dump_json()),
        )

    def recent_events(self, limit: int = 200) -> list[JournalEvent]:
        rows = self._exec(
            "SELECT payload FROM events ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
        return [JournalEvent.model_validate(json.loads(r[0])) for r in rows]

    def gate_stats(self) -> list[GateStat]:
        rows = self._exec(
            "SELECT payload FROM events WHERE type='gate_verdict' ORDER BY ts DESC LIMIT 2000"
        ).fetchall()
        stats: dict[str, dict] = {}
        for r in rows:
            ev = json.loads(r[0])
            results = ev.get("data", {}).get("results", [])
            for g in results:
                name = g.get("gate")
                if name not in stats:
                    stats[name] = {"passed": 0, "rejected": 0, "last": None}
                if g.get("passed"):
                    stats[name]["passed"] += 1
                else:
                    stats[name]["rejected"] += 1
                stats[name]["last"] = "pass" if g.get("passed") else "reject"
        order = ["SANITY", "REGIME", "VRP_EDGE", "EVENT_RISK", "DEFINED_RISK", "LIQUIDITY",
                 "CREDIT_QUALITY", "POSITION_SIZE", "PORTFOLIO_RISK", "CONCENTRATION",
                 "DUPLICATE", "DAILY_HALT"]
        return [
            GateStat(
                gate=name,  # type: ignore[arg-type]
                passed=stats[name]["passed"],
                rejected=stats[name]["rejected"],
                last_verdict=stats[name]["last"],
            )
            for name in order if name in stats
        ]

    def equity_points(self, limit: int = 500) -> list[dict]:
        rows = self._exec(
            "SELECT payload FROM events WHERE type='equity_tick' ORDER BY ts ASC"
        ).fetchall()
        out = []
        for r in rows:
            d = json.loads(r[0])
            eq = d.get("data", {}).get("equity")
            if eq is not None:
                out.append({"ts": d.get("ts"), "equity": eq})
        return out[-limit:]

    # ---------------- asks

    def save_ask(self, req: AskRequest) -> None:
        self._exec(
            "INSERT OR REPLACE INTO asks VALUES (?,?)", (req.id, req.model_dump_json())
        )

    def update_ask(self, req: AskRequest) -> None:
        self._exec(
            "INSERT OR REPLACE INTO asks VALUES (?,?)", (req.id, req.model_dump_json())
        )

    def pending_asks(self) -> list[AskRequest]:
        rows = self._exec("SELECT payload FROM asks").fetchall()
        out = []
        for r in rows:
            try:
                req = AskRequest.model_validate(json.loads(r[0]))
                if req.status in ("queued", "running"):
                    out.append(req)
            except Exception:
                continue
        return out

    def asks(self, limit: int = 50) -> list[AskRequest]:
        rows = self._exec("SELECT payload FROM asks").fetchall()
        out = []
        for r in rows:
            try:
                out.append(AskRequest.model_validate(json.loads(r[0])))
            except Exception:
                continue
        out.sort(key=lambda a: a.created_ts, reverse=True)
        return out[:limit]


def _iso_age(ts_iso: str) -> float:
    try:
        from datetime import datetime
        ts = datetime.fromisoformat(ts_iso)
        return (utcnow() - ts).total_seconds()
    except Exception:
        return 0.0
