"""Shared schemas — the contract between desk components.

Every structured object that passes between agents, kernel, executor, journal,
and the web UI is defined here. LLM outputs are validated against these models;
free-form language exists only inside debate rounds and narrator copy.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- identifiers

AgentId = Literal["prime", "senti", "toro", "ursa", "verdi", "gate", "xq", "sage", "desk"]
MascotState = Literal[
    "idle", "analyzing", "reading_news", "debating", "trading",
    "celebrating", "post_mortem", "risk_alert", "sleeping",
]
Surface = Literal["api", "mcp", "cli"]

GateName = Literal[
    "SANITY", "REGIME", "VRP_EDGE", "EVENT_RISK", "DEFINED_RISK",
    "LIQUIDITY", "CREDIT_QUALITY", "POSITION_SIZE", "PORTFOLIO_RISK",
    "CONCENTRATION", "DUPLICATE", "DAILY_HALT",
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- market data

class AccountView(BaseModel):
    account_number: str
    paper: bool = True
    equity: float
    cash: float
    buying_power: float
    day_pnl: float = 0.0
    total_pnl: float = 0.0
    baseline: float = 100000.0
    options_level: int | None = None
    as_of: datetime = Field(default_factory=utcnow)


class ClockView(BaseModel):
    open: bool
    timestamp: datetime = Field(default_factory=utcnow)
    next_open: datetime | None = None
    next_close: datetime | None = None
    phase: Literal["pre", "open", "closed"] = "closed"


class Candidate(BaseModel):
    symbol: str
    price: float
    momentum_pct: float = 0.0
    volume_note: str | None = None
    optionable: bool = True
    reason: str = ""


class OptionChainEntry(BaseModel):
    option_symbol: str
    underlying: str
    strike: float
    expiry: str
    option_type: Literal["call", "put"]
    bid: float | None = None
    ask: float | None = None
    mid: float | None = None
    spread_pct: float | None = None
    open_interest: int | None = None
    volume: int | None = None
    iv: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None


class NewsArticle(BaseModel):
    id: str
    headline: str
    source: str
    url: str | None = None
    summary: str | None = None
    ts: datetime | None = None
    symbols: list[str] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    """L1 memory — one per cycle."""
    ts: datetime = Field(default_factory=utcnow)
    cycle_id: str
    prices: dict[str, float] = Field(default_factory=dict)
    vix: float | None = None
    iv_rank: dict[str, float] = Field(default_factory=dict)
    screener: list[Candidate] = Field(default_factory=list)
    notes: str = ""


class Regime(BaseModel):
    band: Literal["calm", "choppy", "stressed"]
    vix: float
    gex_sign: int = 1
    iv_rank: float | None = None
    summary: str = ""


# ---------------------------------------------------------------- analysts

class Fact(BaseModel):
    id: str
    label: str
    value: float | str
    unit: str | None = None


class AnalystReport(BaseModel):
    analyst: Literal["trend", "ivr", "gex", "liquidity", "event_risk"]
    symbol: str
    facts: list[Fact] = Field(default_factory=list)
    summary: str = ""
    concerns: list[str] = Field(default_factory=list)
    as_of: datetime = Field(default_factory=utcnow)


class SourceLean(BaseModel):
    source: str
    credibility: float
    lean: float
    headline: str | None = None
    note: str | None = None


class ExpertConsensus(BaseModel):
    lean: float
    summary: str


class SentimentReport(BaseModel):
    """Senti's strict output — AGENTS.md §4."""
    symbol: str
    public_sentiment: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    source_breakdown: list[SourceLean] = Field(default_factory=list)
    expert_consensus: ExpertConsensus | None = None
    event_flags: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    as_of: datetime = Field(default_factory=utcnow)
    model: str = ""


# ---------------------------------------------------------------- debate

class DebateClaim(BaseModel):
    fact_ref: str
    argument: str


class DebateRound(BaseModel):
    round: Literal[1, 2]
    agent: Literal["toro", "ursa"]
    claims: list[DebateClaim] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    conviction: float = Field(ge=0.0, le=1.0)


class Verdict(BaseModel):
    direction: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    conviction: float = Field(ge=0.0, le=1.0)
    key_factor: str = ""
    weakest_link: str = ""
    model: str = ""


# ---------------------------------------------------------------- structures

class Leg(BaseModel):
    option_symbol: str
    side: Literal["buy", "sell"]
    ratio: int = 1
    strike: float
    option_type: Literal["call", "put"]


class StructureSpec(BaseModel):
    kind: Literal["bull_put_spread", "bear_call_spread", "iron_condor", "csp"]
    intent: str  # coid token: bps | bcs | ic | csp
    symbol: str
    legs: list[Leg]
    expiry: str
    dte: int
    width: float
    credit: float  # per-unit net credit
    max_loss: float  # per-unit max loss (width - credit; CSP: strike - credit)
    contracts: int
    premium_risk: float  # total $ at risk
    pop: float | None = None
    expected_move: float | None = None
    notes: str = ""


class OrderReceipt(BaseModel):
    coid: str
    broker_order_id: str | None = None
    status: str
    filled_avg_price: float | None = None
    filled_qty: float | None = None
    surface: Surface = "api"
    submitted_at: datetime = Field(default_factory=utcnow)
    raw: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------- kernel

class GateResult(BaseModel):
    gate: GateName
    passed: bool
    reason_code: str | None = None
    detail: str = ""


class GateVerdict(BaseModel):
    approved: bool
    results: list[GateResult]
    coid: str
    score: int = 0  # how many of the 12 passed


class ExitDecision(BaseModel):
    rule: Literal["profit_target", "hard_stop", "time_stop", "event_close", "regime_flip", "weekend_safety"]
    detail: str = ""
    pnl_est: float = 0.0


# ---------------------------------------------------------------- memory (L2/L3)

class PositionLedger(BaseModel):
    """L2 — the full context of an open position."""
    coid: str
    cycle_id: str
    symbol: str
    kind: str
    spec: StructureSpec
    thesis: str
    verdict: Verdict
    sentiment: SentimentReport | None = None
    debate: list[DebateRound] = Field(default_factory=list)
    entry_ts: datetime = Field(default_factory=utcnow)
    entry_credit: float = 0.0
    exit_rules: dict[str, Any] = Field(default_factory=dict)


class PositionView(BaseModel):
    id: str
    coid: str
    symbol: str
    kind: str
    qty: float
    entry_ts: datetime
    entry_credit: float
    # None = no live quote available; the UI renders an honest "—" instead of
    # fabricating a mark. Never default these to a made-up number.
    current_mark: float | None = None
    unrealized_pnl: float | None = None
    unrealized_pnl_pct: float | None = None
    dte: int = 0
    exit_status: Literal[
        "held", "tp_hit", "stop_hit", "time_stop", "event_close",
        "regime_flip", "expired", "closed_manual",
    ] = "held"
    legs: list[Leg] = Field(default_factory=list)
    thesis: str = ""
    verdict: Verdict | None = None


class ParamProposal(BaseModel):
    param: str
    current: float
    proposed: float
    status: Literal["pending", "applied", "rejected"] = "pending"
    reason: str = ""


class AppliedParam(BaseModel):
    param: str
    before: float
    after: float
    applied_at: datetime = Field(default_factory=utcnow)
    motivated_by: str = ""  # losing trade coid


class Lesson(BaseModel):
    """L3 — Sage's distilled, boolean-checkable lesson."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    text: str
    root_cause: Literal["thesis_wrong", "event_risk_underweighted", "timing_bad", "regime_shift", "luck"]
    failed_signal: str = ""
    missed_check: str = ""
    trade_coid: str = ""
    param_proposals: list[ParamProposal] = Field(default_factory=list)
    created_ts: datetime = Field(default_factory=utcnow)
    applied_count: int = 0
    blocked_trades: list[str] = Field(default_factory=list)
    model: str = ""


# ---------------------------------------------------------------- ask copilot

class AskRequest(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    text: str
    symbols: list[str] = Field(default_factory=list)
    intent: Literal["analyze", "invest", "hedge", "explain"] | None = None
    status: Literal["queued", "running", "answered", "rejected"] = "queued"
    created_ts: datetime = Field(default_factory=utcnow)
    result_summary: str | None = None
    decision_coid: str | None = None
    cycle_id: str | None = None


# ---------------------------------------------------------------- journal / events

class JournalEvent(BaseModel):
    """The atom of observability — appended to JSONL, streamed over SSE."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    ts: datetime = Field(default_factory=utcnow)
    cycle_id: str = ""
    agent: AgentId
    type: str
    symbol: str | None = None
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    surface: Surface | None = None
    model: str | None = None
    level: Literal["info", "warn", "error"] = "info"

    def sse(self) -> str:
        return self.model_dump_json()


class CycleSummary(BaseModel):
    cycle_id: str
    started: datetime = Field(default_factory=utcnow)
    ended: datetime | None = None
    candidates_considered: int = 0
    structures_proposed: int = 0
    orders_placed: int = 0
    rejections: int = 0
    lessons_added: int = 0
    halted: bool = False


# ---------------------------------------------------------------- desk state (GET /state)

class AgentCard(BaseModel):
    id: AgentId
    name: str
    role: str
    ink: str
    state: MascotState = "idle"
    task: str = ""
    last_output: str = ""
    model: str | None = None


class Kpis(BaseModel):
    portfolio_value: float = 0.0
    today_pnl: float = 0.0
    total_pnl: float = 0.0
    risk_used_pct: float = 0.0
    open_risk_pct: float = 0.0


class EquityPoint(BaseModel):
    ts: datetime
    equity: float


class GateStat(BaseModel):
    gate: GateName
    passed: int = 0
    rejected: int = 0
    last_verdict: str | None = None


class MarketInfo(BaseModel):
    open: bool = False
    phase: Literal["pre", "open", "closed"] = "closed"
    next_open: datetime | None = None
    next_close: datetime | None = None


class DeskState(BaseModel):
    """Full snapshot the UI renders on load; SSE events update it live."""
    as_of: datetime = Field(default_factory=utcnow)
    version: str = "0.1.0"
    market: MarketInfo = Field(default_factory=MarketInfo)
    account: AccountView | None = None
    kpis: Kpis = Field(default_factory=Kpis)
    equity_curve: list[EquityPoint] = Field(default_factory=list)
    positions: list[PositionView] = Field(default_factory=list)
    agents: list[AgentCard] = Field(default_factory=list)
    cycles: dict[str, Any] = Field(default_factory=dict)
    halts: list[str] = Field(default_factory=list)
    ask_queue: list[AskRequest] = Field(default_factory=list)
    recent_events: list[JournalEvent] = Field(default_factory=list)
    lessons: list[Lesson] = Field(default_factory=list)
    gate_stats: list[GateStat] = Field(default_factory=list)
    param_history: list[AppliedParam] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    test_mode: bool = False
    paused: bool = False
