"""Configuration — single source of truth for env, risk constants, cast, LLM routing.

Changes to risk constants enter ONLY via Sage's reviewed restrict-only proposals
(see kernel/gates.py validate_param_proposal) or a journaled OPERATOR_OVERRIDE.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
JOURNAL_PATH = DATA_DIR / "journal" / "events.jsonl"
DB_PATH = DATA_DIR / "stonks.db"
CONFIG_HISTORY_PATH = DATA_DIR / "config_history.json"


# ---------------------------------------------------------------- env

def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


@dataclass
class Env:
    alpaca_key: str = field(default_factory=lambda: env("ALPACA_API_KEY"))
    alpaca_secret: str = field(default_factory=lambda: env("ALPACA_SECRET_KEY"))
    alpaca_mode: str = field(default_factory=lambda: env("ALPACA_MODE", "paper"))
    gemini_key: str = field(default_factory=lambda: env("GEMINI_API_KEY"))
    openai_key: str = field(default_factory=lambda: env("OPENAI_API_KEY"))
    featherless_key: str = field(default_factory=lambda: env("FEATHERLESS_API_KEY"))
    desk_paused: bool = field(default_factory=lambda: env("DESK_PAUSED", "false").lower() == "true")
    test_mode: bool = field(default_factory=lambda: env("STONKS_TEST", "false").lower() == "true")
    tick_seconds: int = field(default_factory=lambda: int(env("TICK_SECONDS", "1800")))
    cors_origin: str = field(default_factory=lambda: env("CORS_ALLOW_ORIGIN", "*"))

    @property
    def has_alpaca(self) -> bool:
        return bool(self.alpaca_key) and bool(self.alpaca_secret)


ENV = Env()


# ---------------------------------------------------------------- risk constants (RISK.md §1–§5)

@dataclass
class RiskConfig:
    # gates
    quote_max_age_seconds: int = 120
    vix_entry_ceiling: float = 35.0            # bound 20..35 (may only decrease)
    vix_stressed: float = 30.0
    vix_choppy: float = 20.0
    vrp_min_edge: float = 0.02                 # implied-vs-realized edge
    event_blackout_hours: int = 24             # bound 12..48 (may only increase)
    min_oi: int = 250
    max_spread_pct: float = 0.25
    min_credit_pct_of_width: float = 0.15
    max_position_size_pct: float = 0.01       # 1.0% NAV — bound .25%..1% (may only decrease)
    max_portfolio_risk_pct: float = 0.05       # 5% NAV
    max_structures_per_underlying: int = 2
    daily_halt_pct: float = 0.02               # 2% NAV — bound 1%..2.5% (may only decrease)
    min_iv_rank: float = 20.0                  # bound 10..35
    # exits
    profit_target_pct: float = 0.50            # of max credit
    hard_stop_multiple: float = 2.0            # × credit received
    time_stop_dte: int = 21
    wheel_roll_dte: int = 21
    # sage
    post_mortem_trigger_pct: float = -0.08     # bound -5%..-12%
    post_mortem_trigger_closed: float = 0.50   # loss ≥ 50% of max risk on close
    lesson_cap: int = 50
    # sizing
    wheel_notional_pct: float = 0.05
    credit_floor: float = 0.20                 # $/contract minimum credit
    # universe
    watchlist: tuple = ("SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "TSLA")
    max_candidates: int = 3
    target_dte_min: int = 30
    target_dte_max: int = 45
    delta_short: float = 0.16
    delta_wing: float = 0.08
    min_wing_width: float = 1.0

    def snapshot(self) -> dict:
        d = asdict(self)
        d["watchlist"] = list(self.watchlist)
        return d


RISK = RiskConfig()


# ---------------------------------------------------------------- restrict-only bounds (RISK.md §3)
# direction: "increase" means Sage may only move it up (blackout hours, min IVR floor)
#             "decrease" means Sage may only move it down (sizes, ceilings, halt)

PARAM_BOUNDS: dict[str, dict] = {
    "event_blackout_hours": {"min": 12, "max": 48, "direction": "increase"},
    "min_iv_rank": {"min": 10, "max": 35, "direction": "increase"},
    "max_position_size_pct": {"min": 0.0025, "max": 0.01, "direction": "decrease"},
    "daily_halt_pct": {"min": 0.01, "max": 0.025, "direction": "decrease"},
    "vix_entry_ceiling": {"min": 20, "max": 35, "direction": "decrease"},
    "vrp_min_edge": {"min": 0.01, "max": 0.10, "direction": "increase"},
    "min_credit_pct_of_width": {"min": 0.10, "max": 0.35, "direction": "increase"},
}


def validate_param_proposal(param: str, current: float, proposed: float) -> tuple[bool, str]:
    """Restrict-only enforcement — pure code, not prompts (RISK.md §3)."""
    bounds = PARAM_BOUNDS.get(param)
    if bounds is None:
        return False, f"UNKNOWN_PARAM:{param}"
    lo, hi, direction = bounds["min"], bounds["max"], bounds["direction"]
    if not (lo <= proposed <= hi):
        return False, f"OUT_OF_BOUNDS:{param} must stay in [{lo}, {hi}]"
    if direction == "increase" and proposed <= current:
        return False, f"NOT_RESTRICTIVE:{param} may only increase (current {current})"
    if direction == "decrease" and proposed >= current:
        return False, f"NOT_RESTRICTIVE:{param} may only decrease (current {current})"
    return True, "ok"


def apply_param(param: str, value: float, motivated_by: str = "") -> bool:
    """Apply a validated proposal to the live RISK object + log to config history."""
    ok, why = validate_param_proposal(param, getattr(RISK, param), value)
    if not ok:
        return False
    before = getattr(RISK, param)
    setattr(RISK, param, type(before)(value))
    history = load_config_history()
    history.append({
        "param": param, "before": before, "after": value,
        "motivated_by": motivated_by, "ts": __import__("stonks.schemas", fromlist=["utcnow"]).utcnow().isoformat(),
    })
    _save_json(CONFIG_HISTORY_PATH, history)
    return True


def load_config_history() -> list[dict]:
    return _load_json(CONFIG_HISTORY_PATH, [])


def _load_json(p: Path, default):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _save_json(p: Path, payload) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- LLM routing (ARCHITECTURE §2.3)

@dataclass
class LLMRoute:
    role: str
    primary: str          # provider id: gemini | openai | featherless
    model: str
    fallbacks: list[str] = field(default_factory=list)


LLM_ROUTES: dict[str, LLMRoute] = {
    "senti": LLMRoute("senti", "gemini", "gemini-2.0-flash", ["openai"]),
    "debate": LLMRoute("debate", "gemini", "gemini-2.0-flash", ["openai"]),
    "narrator": LLMRoute("narrator", "gemini", "gemini-2.0-flash", ["openai"]),
    "judge": LLMRoute("judge", "openai", "gpt-4o", ["gemini"]),
    "structurer": LLMRoute("structurer", "openai", "gpt-4o", ["gemini"]),
    "sage": LLMRoute("sage", "openai", "gpt-4o", ["gemini"]),
    "partner": LLMRoute("partner", "featherless", "featherless/quill-72b", ["gemini"]),
}


# ---------------------------------------------------------------- cast (BRAND-AND-MASCOTS §3)

CAST: list[dict] = [
    {"id": "prime", "name": "Stonks Prime", "role": "Orchestrator & narrator", "ink": "#F8F8F8",
     "prop": "arms", "quip": "The desk is open.",
     "states": ["idle", "analyzing", "celebrating", "sleeping", "risk_alert"]},
    {"id": "senti", "name": "Senti", "role": "Sentiment analyst", "ink": "#4DA3FF",
     "prop": "phone", "quip": "Fourteen articles. Three mention earnings.",
     "states": ["idle", "reading_news", "analyzing", "sleeping"]},
    {"id": "toro", "name": "Toro", "role": "Bull researcher", "ink": "#00FF87",
     "prop": "horns", "quip": "Momentum is a friend.",
     "states": ["idle", "debating", "celebrating", "sleeping"]},
    {"id": "ursa", "name": "Ursa", "role": "Bear researcher", "ink": "#FF4D5E",
     "prop": "umbrella", "quip": "It's expensive to be this right.",
     "states": ["idle", "debating", "risk_alert", "sleeping"]},
    {"id": "verdi", "name": "Verdi", "role": "Judge", "ink": "#C77DFF",
     "prop": "gavel", "quip": "Verdict.",
     "states": ["idle", "analyzing", "debating", "sleeping"]},
    {"id": "gate", "name": "Sgt. Gate", "role": "Risk kernel", "ink": "#FFB020",
     "prop": "clipboard", "quip": "Twelve gates. Zero exceptions.",
     "states": ["idle", "analyzing", "risk_alert", "sleeping"]},
    {"id": "xq", "name": "XQ", "role": "Executor", "ink": "#00E5FF",
     "prop": "stamp", "quip": "Filled.",
     "states": ["idle", "trading", "celebrating", "sleeping"]},
    {"id": "sage", "name": "Sage", "role": "Post-mortem & learning", "ink": "#FF8A3D",
     "prop": "lightbulb", "quip": "We lost. We learned.",
     "states": ["idle", "post_mortem", "analyzing", "sleeping"]},
]


# ---------------------------------------------------------------- events calendar (static, for tests / fallback)

# Known macro events during the hackathon window (UTC dates, hour = 13:30 ET approx).
EVENTS: list[dict] = [
    {"symbol": "INDEX", "kind": "FOMC", "date": "2026-09-02"},
    {"symbol": "INDEX", "kind": "CPI", "date": "2026-09-03"},
    {"symbol": "SPY", "kind": "FOMC", "date": "2026-09-02"},
    {"symbol": "QQQ", "kind": "FOMC", "date": "2026-09-02"},
]

# Earnings dates for the watchlist (approximate; the event analyst prefers live
# corporate-actions/calendar data and falls back to this table).
EARNINGS: dict[str, str] = {
    "AAPL": "2026-10-01",
    "MSFT": "2026-10-15",
    "NVDA": "2026-08-26",
    "TSLA": "2026-10-13",
}


def ensure_dirs() -> None:
    for p in (DATA_DIR, JOURNAL_PATH.parent, DB_PATH.parent):
        p.mkdir(parents=True, exist_ok=True)
