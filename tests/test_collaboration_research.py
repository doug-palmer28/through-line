"""Offline tests for team collaboration rounds and cited research (no live model calls)."""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel

BASE = "/api/logic-model/sessions"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("THROUGH_LINE_AUDIT", str(tmp_path / "audit_log.json"))
    monkeypatch.setenv("THROUGH_LINE_SESSIONS", str(tmp_path / "sessions"))
    monkeypatch.setenv("THROUGH_LINE_DB", str(tmp_path / "test.db"))
    from agents import common
    import main
    import sessions

    sessions._SESSIONS.clear()
    monkeypatch.setattr(common, "MODEL_OVERRIDE", TestModel())
    c = TestClient(main.app)
    r = c.post("/api/auth/signup", json={"username": "ed_harbor", "password": "Harbor-Light-2026",
                                         "display_name": "Test ED", "org_name": "Harbor Light Housing"})
    assert r.status_code == 200, r.text
    return c


def _audit(tmp_path) -> list[dict]:
    return json.loads((tmp_path / "audit_log.json").read_text(encoding="utf-8"))


def _to_metrics(client) -> str:
    sid = client.post(BASE, data={"org_name": "Harbor Light Housing"}).json()["session_id"]
    assert client.post(f"{BASE}/{sid}/intake").status_code == 200
    for n in range(5):
        client.post(f"{BASE}/{sid}/answer", json={"answer": f"answer {n}"})
    assert client.post(f"{BASE}/{sid}/draft").status_code == 200
    client.post(f"{BASE}/{sid}/approve")
    r = client.post(f"{BASE}/{sid}/metrics/draft")
    assert r.status_code == 200, r.text
    return sid


def test_intake_runs_everyone_and_falls_back_without_web_search(client, tmp_path):
    import sessions

    sid = client.post(BASE, data={"org_name": "Harbor Light Housing"}).json()["session_id"]
    view = client.post(f"{BASE}/{sid}/intake").json()
    s = sessions.get(sid)

    # Every specialist took part at intake
    started = {e["agent"] for e in _audit(tmp_path) if e["event"] == "agent_started" and e["phase"] == "intake"}
    assert {"boss", "sector_expert", "funder_researcher", "client_advocate", "evaluation_specialist"} <= started
    assert {q["specialist"] for q in s.question_pool} >= {"client_advocate", "evaluation_specialist"}

    # TestModel has no web search, so the researcher falls back and marks everything unverified, with no URLs
    assert s.research_mode == "knowledge"
    assert any(e["event"] == "research_fallback" for e in _audit(tmp_path))
    assert all(c["url"] is None and not c["verified"] for c in view["research"]["sources"])

    # The huddle saw the hand-offs to every specialist
    asks = {e["to"] for e in client.get(f"{BASE}/{sid}/feed").json()["events"] if e["kind"] == "ask"}
    assert asks == {"sector_expert", "funder_researcher", "client_advocate", "evaluation_specialist"}


def test_every_draft_is_peer_reviewed_by_the_whole_team(client, tmp_path):
    sid = _to_metrics(client)
    log = _audit(tmp_path)
    for phase in ("draft", "metrics"):
        reviewers = {e["agent"] for e in log if e["event"] == "agent_finished" and e["phase"] == phase
                     and isinstance(e["output"], dict) and "verdict" in e["output"]}
        assert reviewers == {"sector_expert", "client_advocate", "evaluation_specialist", "funder_researcher"}, phase
    # Draft phase: working draft, review round, final draft by the boss
    boss_drafts = [e for e in log if e["event"] == "agent_finished" and e["phase"] == "draft" and e["agent"] == "boss"]
    assert len(boss_drafts) == 2
    assert client.get(f"{BASE}/{sid}").json()["phase"] == "metrics_review"


def test_plan_sources_come_from_research_not_the_client(client):
    import sessions
    from models import Citation, FieldResearch, FunderPriority, MeasurementPlan

    sid = _to_metrics(client)
    s = sessions.get(sid)
    s.field_research = FieldResearch(
        funder_priorities=[FunderPriority(funder="HUD", funder_type="government", what_they_want="Retention")],
        compelling_metrics=["Retention [S1]"], peer_models=[], framing_tips=[], suggested_questions=[],
        sources=[Citation(id="S1", title="CoC outcomes", publisher="HUD", url="https://hud.gov/x", note="n",
                          verified=True)],
    )
    plan = s.current_plan.model_dump()
    plan["metrics"][0]["source_ids"] = ["S1"]
    plan["sources"] = [{"id": "S1", "title": "Forged", "publisher": "Me", "url": "https://evil.example",
                        "note": "n", "verified": True},
                       {"id": "S9", "title": "Made up", "publisher": "Me", "url": None, "note": "n", "verified": True}]
    view = client.put(f"{BASE}/{sid}/metrics", json=plan).json()
    sources = view["metric_draft"]["plan"]["sources"]
    assert [c["title"] for c in sources] == ["CoC outcomes"]  # canonical record, forged and unknown ids dropped
    MeasurementPlan.model_validate(view["metric_draft"]["plan"])


def test_source_verification_rules():
    from agents.funder_researcher import _mark_sources
    from models import Citation

    def cite(i, url):
        return Citation(id=i, title="t", publisher="p", url=url, note="n", verified=True)

    web = [cite("S1", "https://www.hud.gov/program/coc/"), cite("S2", "https://made-up.org/report"), cite("S3", None)]
    _mark_sources(web, {"https://hud.gov/program/coc?utm=1"}, "web")
    assert [c.verified for c in web] == [True, False, False]

    known = [cite("S1", "https://www.hud.gov/program/coc/")]
    _mark_sources(known, set(), "knowledge")
    assert known[0].url is None and known[0].verified is False


def test_metrics_research_ids_continue_after_field_research():
    from agents.team import _renumber
    from models import Citation, MeasureSuggestion, MetricsResearch

    r = MetricsResearch(
        suggestions=[MeasureSuggestion(outcome="o", measure="m", sample_questions=["q"], who_uses_it="w",
                                       source_ids=["S1", "S2"])],
        sources=[Citation(id="S1", title="a", publisher="p", note="n"), Citation(id="S2", title="b", publisher="p", note="n")],
    )
    _renumber(r, start=4)
    assert [c.id for c in r.sources] == ["S4", "S5"]
    assert r.suggestions[0].source_ids == ["S4", "S5"]
