"""Agent tests — deterministic fallbacks, credibility recompute, Sage restrict-only."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from stonks.agents.debate import judge, run_debate
from stonks.agents.llm import LLMClient, LLMBusError
from stonks.agents.narrator import narrate
from stonks.agents.sage import post_mortem
from stonks.agents.analysts import CodeAnalysts
from stonks.agents.senti import SentiAgent
from stonks.memory.store import MemoryStore
from stonks.schemas import (
    AskRequest,
    JournalEvent,
    Lesson,
    NewsArticle,
    PositionLedger,
    SentimentReport,
    StructureSpec,
    Verdict,
    utcnow,
)
from stonks import fixtures
from stonks.config import RISK


class FakeLLM(LLMClient):
    def __init__(self, responses=None):
        super().__init__(test_mode=True)
        self.responses = responses or {}
        self.calls = []

    async def complete(self, route, system, user, json_mode=True):
        self.calls.append((route, user[:80]))
        if route in self.responses:
            return self.responses[route]
        raise LLMBusError("fake bus down")


def news(headline, source="Reuters", url="https://x/1"):
    return NewsArticle(id="n", headline=headline, source=source, url=url, symbols=["SPY"])


class TestSenti:
    def test_fallback_positive(self):
        agent = SentiAgent(llm=FakeLLM())
        r = asyncio.run(agent.analyze("SPY", [news("Markets rally on strong data")], []))
        assert r.public_sentiment > 0
        assert r.confidence <= 0.5
        assert "https://x/1" in r.citations

    def test_fallback_negative(self):
        agent = SentiAgent(llm=FakeLLM())
        r = asyncio.run(agent.analyze("SPY", [news("Stocks slump as fear spreads")], []))
        assert r.public_sentiment < 0

    def test_fallback_neutral(self):
        agent = SentiAgent(llm=FakeLLM())
        r = asyncio.run(agent.analyze("SPY", [news("Quiet session in the markets")], []))
        assert r.public_sentiment == 0.0

    def test_credibility_recompute_overrides_llm_aggregate(self):
        fake = FakeLLM({
            "senti": {
                "symbol": "SPY", "public_sentiment": 0.9, "confidence": 0.9,
                "source_breakdown": [
                    {"source": "Reuters", "lean": -0.8, "headline": "a"},
                    {"source": "Reuters", "lean": -0.8, "headline": "b"},
                    {"source": "SeekingAlpha", "lean": 0.8, "headline": "c"},
                ],
                "expert_consensus": {"lean": 0.1, "summary": "x"},
                "event_flags": [], "citations": ["https://x/1"],
            }
        })
        agent = SentiAgent(llm=fake)
        r = asyncio.run(agent.analyze("SPY", [news("a")], []))
        assert r.public_sentiment < 0.5

    def test_no_citations_halves_confidence(self):
        fake = FakeLLM({
            "senti": {
                "symbol": "SPY", "public_sentiment": 0.5, "confidence": 0.8,
                "source_breakdown": [{"source": "Reuters", "lean": 0.5, "headline": "a"}],
                "expert_consensus": {"lean": 0.1, "summary": "x"},
                "event_flags": [], "citations": [],
            }
        })
        agent = SentiAgent(llm=fake)
        r = asyncio.run(agent.analyze("SPY", [news("a")], []))
        assert r.confidence <= 0.4


def make_reports():
    a = CodeAnalysts()
    return a.analyze("SPY", [], 505.0, [], iv_rank=30.0, vix=15.0, events_hours=48.0)


def make_sentiment():
    return SentimentReport(symbol="SPY", public_sentiment=0.3, confidence=0.6)


class TestDebate:
    def test_fallback_four_rounds_fact_refd(self):
        reports = make_reports()
        rounds = asyncio.run(run_debate(reports, make_sentiment(), [], llm=FakeLLM()))
        assert len(rounds) == 4
        valid = {f.id for r in reports for f in r.facts} | {"senti.score", "senti.flags", "senti.experts"}
        for r in rounds:
            assert r.claims
            for c in r.claims:
                assert c.fact_ref in valid or c.fact_ref.startswith("senti")

    def test_judge_fallback_bullish(self):
        rounds = asyncio.run(run_debate(make_reports(), make_sentiment(), [], llm=FakeLLM()))
        for r in rounds:
            if r.agent == "toro":
                r.conviction = 0.9
            else:
                r.conviction = 0.1
        v = asyncio.run(judge(rounds, make_reports(), make_sentiment(), llm=FakeLLM()))
        assert v.direction == "BULLISH"

    def test_judge_fallback_ursa_wins(self):
        rounds = asyncio.run(run_debate(make_reports(), make_sentiment(), [], llm=FakeLLM()))
        for r in rounds:
            if r.agent == "ursa":
                r.conviction = 0.95
            else:
                r.conviction = 0.1
        v = asyncio.run(judge(rounds, make_reports(), make_sentiment(), llm=FakeLLM()))
        assert v.direction == "BEARISH"


def make_ledger():
    spec = StructureSpec(
        kind="iron_condor", intent="ic", symbol="SPY", legs=[],
        expiry="2026-10-16", dte=40, width=20.0, credit=1.5,
        max_loss=18.5, contracts=1, premium_risk=1850.0,
    )
    return PositionLedger(
        coid="stonks-ic-SPY-TEST", cycle_id="c1", symbol="SPY", kind="iron_condor",
        spec=spec, thesis="test", verdict=Verdict(direction="NEUTRAL", conviction=0.6,
        key_factor="t"), entry_ts=utcnow(), entry_credit=1.5,
    )


class TestSage:
    def test_happy_path_applies_tightening(self, tmp_path, monkeypatch):
        monkeypatch.setattr("stonks.config.CONFIG_HISTORY_PATH", tmp_path / "h.json")
        monkeypatch.setattr(RISK, "event_blackout_hours", 24)
        fake = FakeLLM({"sage": dict(fixtures.SAGE_POST_MORTEM)})
        lesson = asyncio.run(post_mortem(make_ledger(), [], -900.0, llm=fake))
        assert lesson.root_cause == "event_risk_underweighted"
        assert any(p.status == "applied" for p in lesson.param_proposals)
        assert RISK.event_blackout_hours == 36
        monkeypatch.setattr(RISK, "event_blackout_hours", 24)

    def test_loosening_rejected(self, tmp_path, monkeypatch):
        monkeypatch.setattr("stonks.config.CONFIG_HISTORY_PATH", tmp_path / "h.json")
        monkeypatch.setattr(RISK, "event_blackout_hours", 36)
        payload = dict(fixtures.SAGE_POST_MORTEM)
        payload["param_proposals"] = [{"param": "event_blackout_hours", "current": 36, "proposed": 12}]
        fake = FakeLLM({"sage": payload})
        lesson = asyncio.run(post_mortem(make_ledger(), [], -900.0, llm=fake))
        assert all(p.status == "rejected" for p in lesson.param_proposals)
        assert RISK.event_blackout_hours == 36
        monkeypatch.setattr(RISK, "event_blackout_hours", 24)

    def test_fallback_lesson(self):
        lesson = asyncio.run(post_mortem(make_ledger(), [], -900.0, llm=FakeLLM()))
        assert lesson.text


class TestNarrator:
    def test_fallback_phrases(self):
        events = [
            JournalEvent(agent="senti", type="senti_report", summary="read the news", data={}),
            JournalEvent(agent="xq", type="order_filled", summary="got filled", data={}),
        ]
        lines = asyncio.run(narrate(events, llm=FakeLLM()))
        assert len(lines) == 2
        assert "Senti" in lines[0] and "news" in lines[0]


class TestMemoryStore:
    def make_store(self, tmp_path):
        return MemoryStore(db_path=tmp_path / "t.db")

    def test_lesson_roundtrip_and_cap(self, tmp_path):
        store = self.make_store(tmp_path)
        for i in range(52):
            store.save_lesson(Lesson(text=f"L{i}", root_cause="luck", created_ts=utcnow()))
        assert len(store.lessons()) == 50

    def test_lesson_applied_tracking(self, tmp_path):
        store = self.make_store(tmp_path)
        l = Lesson(text="block X", root_cause="luck")
        store.save_lesson(l)
        store.record_lesson_applied(l.id, "stonks-ic-X-1")
        got = store.lessons()[0]
        assert got.applied_count == 1 and "stonks-ic-X-1" in got.blocked_trades

    def test_position_lifecycle(self, tmp_path):
        store = self.make_store(tmp_path)
        ledger = make_ledger()
        store.save_position(ledger)
        assert len(store.open_positions()) == 1
        store.mark_closed(ledger.coid, utcnow(), -120.0, "hard_stop")
        assert store.open_positions() == []
        closed, pnl = store.closed_positions()[0]
        assert closed.coid == ledger.coid and pnl == -120.0

    def test_ask_queue(self, tmp_path):
        store = self.make_store(tmp_path)
        req = AskRequest(text="invest in NVDA", symbols=["NVDA"])
        store.save_ask(req)
        assert len(store.pending_asks()) == 1
        req.status = "answered"
        store.update_ask(req)
        assert store.pending_asks() == []
        assert len(store.asks()) == 1

    def test_gate_stats_aggregation(self, tmp_path):
        store = self.make_store(tmp_path)
        ev = JournalEvent(
            agent="gate", type="gate_verdict", summary="verdict",
            data={"results": [
                {"gate": "SANITY", "passed": True, "reason_code": None, "detail": ""},
                {"gate": "EVENT_RISK", "passed": False, "reason_code": "EVENT_BLACKOUT", "detail": ""},
            ]},
        )
        store.save_event(ev)
        stats = {s.gate: s for s in store.gate_stats()}
        assert stats["SANITY"].passed == 1
        assert stats["EVENT_RISK"].rejected == 1
