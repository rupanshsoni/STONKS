"""FastAPI desk worker — /state, /events (SSE), /ask, /journal, /memory, /risk, /health."""
from __future__ import annotations

import asyncio
import contextlib
import json
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from stonks import __version__
from stonks.alpaca.client import AlpacaClient
from stonks.config import (
    CAST,
    ENV,
    RISK,
    load_config_history,
)
from stonks.journal import EventBus, Journal
from stonks.kernel import snapshot_config
from stonks.memory import MemoryStore
from stonks.orchestrator import Orchestrator
from stonks.schemas import (
    AgentCard,
    AskRequest,
    DeskState,
    JournalEvent,
    Kpis,
    MarketInfo,
    utcnow,
)

app = FastAPI(title="STONKS desk", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ENV.cors_origin] if ENV.cors_origin != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

journal = Journal()
store = MemoryStore()
bus = journal.bus
orch = Orchestrator(journal=journal, store=store, test_mode=ENV.test_mode)
_client = orch.client


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(_scheduler())


async def _scheduler() -> None:
    await asyncio.sleep(2)
    while True:
        try:
            if ENV.desk_paused:
                await asyncio.sleep(30)
                continue
            await orch.tick()
        except Exception as exc:
            journal.emit("desk", "error", f"cycle error: {exc}", level="error",
                         data={"error": str(exc)})
        await asyncio.sleep(ENV.tick_seconds)


@app.get("/health")
async def health() -> dict:
    checks = {
        "db": True,
        "alpaca": True,
        "mcp": False,
    }
    try:
        store.recent_events(1)
    except Exception:
        checks["db"] = False
    try:
        await _client.account()
    except Exception:
        checks["alpaca"] = False
    return {
        "status": "ok" if all(checks.values()) or ENV.test_mode else "degraded",
        "checks": checks,
        "test_mode": ENV.test_mode,
        "version": __version__,
        "ts": utcnow().isoformat(),
    }


@app.get("/state")
async def state() -> DeskState:
    market = MarketInfo()
    account = None
    kpis = Kpis()
    positions: list = []
    try:
        clock = await _client.clock()
        market = MarketInfo(open=clock.open, phase=clock.phase,  # type: ignore[arg-type]
                            next_open=clock.next_open, next_close=clock.next_close)
        account = await _client.account()
        kpis.portfolio_value = account.equity
        kpis.today_pnl = account.day_pnl
        kpis.total_pnl = account.total_pnl
    except Exception:
        account = None

    ledgers = []
    try:
        ledgers = await asyncio.to_thread(store.open_positions)
    except Exception:
        pass
    open_risk = 0.0
    for l in ledgers:
        open_risk += l.spec.premium_risk
        dte = max(l.spec.dte - max((utcnow() - l.entry_ts).days, 0), 0)
        positions.append({
            "id": l.coid, "coid": l.coid, "symbol": l.symbol, "kind": l.spec.kind,
            "qty": float(l.spec.contracts), "entry_ts": l.entry_ts.isoformat(),
            "entry_credit": l.entry_credit, "current_mark": l.entry_credit,
            "unrealized_pnl": 0.0, "unrealized_pnl_pct": 0.0, "dte": dte,
            "exit_status": "held", "legs": [leg.model_dump() for leg in l.spec.legs],
            "thesis": l.thesis, "verdict": l.verdict.model_dump(),
        })
    if account is not None:
        kpis.risk_used_pct = open_risk / max(account.equity, 1.0)
        kpis.open_risk_pct = kpis.risk_used_pct

    equity = []
    try:
        equity = await asyncio.to_thread(store.equity_points, 500)
    except Exception:
        pass
    if not equity and account is not None:
        equity = [{"ts": utcnow().isoformat(), "equity": account.equity}]

    agents = []
    recent = journal.read(60)
    recent_events = recent[:60]
    for c in CAST:
        last = next((e for e in recent_events if e.agent == c["id"]), None)
        agents.append(AgentCard(
            id=c["id"],  # type: ignore[arg-type]
            name=c["name"], role=c["role"], ink=c["ink"],
            state=orch.agent_states.get(c["id"], "idle"),  # type: ignore[arg-type]
            task=orch.agent_tasks.get(c["id"], ""),
            last_output=last.summary if last else c["quip"],
            model=_agent_model(c["id"]),
        ))

    try:
        lessons = await asyncio.to_thread(store.lessons, 50)
    except Exception:
        lessons = []
    try:
        gate_stats = await asyncio.to_thread(store.gate_stats)
    except Exception:
        gate_stats = []
    try:
        asks = await asyncio.to_thread(store.asks, 20)
    except Exception:
        asks = []

    param_history = [
        AppliedParam(param=h.get("param", ""), before=float(h.get("before", 0)),
                     after=float(h.get("after", 0)), applied_ts=h.get("applied_at") or h.get("ts") or "",
                     motivated_by=h.get("motivated_by", ""))
        if isinstance(h.get("applied_at") or h.get("ts"), str) else AppliedParam(param=h.get("param", ""), before=float(h.get("before", 0)), after=float(h.get("after", 0)), motivated_by=h.get("motivated_by", ""))
        for h in load_config_history()
    ]

    return DeskState(
        as_of=utcnow(),
        version=__version__,
        market=market,
        account=account,
        kpis=kpis,
        equity_curve=equity,  # type: ignore[arg-type]
        positions=positions,  # type: ignore[arg-type]
        agents=agents,
        halts=["entries_halted"] if orch.halted_entries else [],
        ask_queue=[a for a in asks],
        recent_events=recent_events[:40],
        lessons=lessons,
        gate_stats=gate_stats,
        param_history=param_history,
        config_snapshot=snapshot_config(),
        test_mode=ENV.test_mode,
        paused=ENV.desk_paused,
    )


@app.get("/events")
async def events(request: Request) -> EventSourceResponse:
    async def gen():
        q = bus.subscribe()
        try:
            yield {"event": "hello", "data": json.dumps({"ts": utcnow().isoformat()})}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    item = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield {"event": "journal", "data": item.sse()}
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            bus.unsubscribe(q)

    return EventSourceResponse(gen())


@app.post("/ask")
async def ask(req: Request) -> dict:
    body = await req.json()
    text = str(body.get("text", ""))[:300].strip()
    if not text:
        return {"error": "empty request"}
    import re
    symbols = re.findall(r"\b[A-Z]{2,5}\b", text.upper())
    known = {"SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "TSLA", "VIXY"}
    symbols = [s for s in symbols if s in known]
    ask_req = AskRequest(text=text, symbols=symbols[:3])
    await asyncio.to_thread(store.save_ask, ask_req)
    journal.emit("desk", "ask_received",
                 f"Copilot request queued: {text}",
                 data={"ask_id": ask_req.id})
    return {"ok": True, "id": ask_req.id, "symbols": ask_req.symbols,
           "status": ask_req.status}


@app.get("/journal")
async def journal_endpoint(limit: int = 500) -> list[dict]:
    events = journal.read(limit)
    return [json.loads(e.model_dump_json()) for e in events]


@app.get("/memory")
async def memory_endpoint() -> dict:
    lessons = await asyncio.to_thread(store.lessons, 50)
    snaps = await asyncio.to_thread(store.snapshots_since, "2000-01-01T00:00:00")
    ledgers = await asyncio.to_thread(store.open_positions)
    closed = await asyncio.to_thread(store.closed_positions)
    return {
        "l3_lessons": [json.loads(l.model_dump_json()) for l in lessons],
        "l1_snapshots": snaps[-30:],
        "l2_open": [json.loads(l.model_dump_json()) for l in ledgers],
        "l2_closed": [
            {"ledger": json.loads(l.model_dump_json()), "exit_pnl": p}
            for l, p in closed
        ],
        "param_history": load_config_history(),
    }


@app.get("/risk")
async def risk_endpoint() -> dict:
    return {
        "config": snapshot_config(),
        "param_bounds": {
            k: v for k, v in __import__("stonks.config", fromlist=["PARAM_BOUNDS"]).PARAM_BOUNDS.items()
        },
        "param_history": load_config_history(),
        "gate_stats": [json.loads(json.dumps(g.model_dump())) for g in await asyncio.to_thread(store.gate_stats)],
    }


def _agent_model(agent_id: str) -> str | None:
    mapping = {
        "senti": "gemini-2.0-flash", "toro": "gemini-2.0-flash",
        "ursa": "gemini-2.0-flash", "verdi": "gpt-4o", "sage": "gpt-4o",
        "gate": None, "xq": None, "prime": "gemini-2.0-flash (narration)",
    }
    return mapping.get(agent_id)
