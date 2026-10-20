"""Studio sessions: state, live team feed, and what is kept where.

What lives where (the privacy design):

| Information                                   | Memory           | data/sessions/<id>.json                      |
|-----------------------------------------------|------------------|----------------------------------------------|
| Uploaded files / website text                 | Only while read  | Never                                        |
| Working notes (snapshot, sector brief,        | While active     | While active, then WIPED when the session    |
| field research, question pool)                |                  | completes, is ended, or expires              |
| What the client types; questions; drafts;     | Yes              | Yes (the session record)                     |
| measurement plan; approvals                   |                  |                                              |
| Live team feed (who is talking to whom)       | Yes              | Never                                        |

Working notes are saved while a session is active only so a server restart
doesn't lose someone's progress. Sessions stay open for SESSION_LIFETIME of
inactivity, because people may take a long time to think through answers.
A completed session never expires: its working notes are already wiped, and the
organization should always be able to see the logic model and plan it approved.
"""

import asyncio
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import PROJECT_DIR
from models import (
    INTERVIEW_QUESTIONS, FieldResearch, LogicModel, MeasurementPlan, MetricsResearch, OrgSnapshot, SectorBrief,
)

SESSION_LIFETIME = timedelta(days=7)  # of inactivity
MAX_REVISIONS = 2  # agent revision rounds for the logic model (token budget)
MAX_METRIC_REVISIONS = 2  # agent revision rounds for the measurement plan
MAX_EXTRA_UPLOADS = 2  # documents the client can add after intake
FEED_LIMIT = 300

PHASES = ["intake", "interview", "ready_to_draft", "review", "ready_for_metrics", "metrics_review", "complete"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def sessions_dir() -> Path:
    return Path(os.getenv("THROUGH_LINE_SESSIONS", PROJECT_DIR / "data" / "sessions"))


@dataclass
class Session:
    id: str
    org_name: str
    org_id: int | None = None  # the organization (staff account) that owns this session
    actor_id: int | None = None  # the staff member making the current request (token ledger; not saved)
    feature: str = "studio"  # which feature's runs these are (token ledger)
    created_at: datetime = field(default_factory=_now)
    last_active: datetime = field(default_factory=_now)
    phase: str = "intake"
    ended: bool = False
    source_text: str | None = None  # uploaded content; held only while the team reads it
    pending_sources: list = field(default_factory=list)  # read at start, consumed by intake (memory only)
    source_manifest: list[dict] = field(default_factory=list)
    snapshot: OrgSnapshot | None = None
    sector_brief: SectorBrief | None = None
    field_research: FieldResearch | None = None
    metrics_research: MetricsResearch | None = None
    research_mode: str | None = None  # "web" (live search) or "knowledge" (fallback, sources unverified)
    question_pool: list[dict] = field(default_factory=list)  # {specialist, question, why}
    questions: list[dict] = field(default_factory=list)  # {number, question, why, answer}
    notes: list[str] = field(default_factory=list)
    drafts: list[dict] = field(default_factory=list)  # {version, source, logic_model}
    revisions_used: int = 0
    approved: LogicModel | None = None
    metric_drafts: list[dict] = field(default_factory=list)  # {version, source, plan}
    metric_revisions_used: int = 0
    approved_plan: MeasurementPlan | None = None
    upload_request: str | None = None  # an optional document the team asked for
    extra_uploads: int = 0
    transcript: list[dict] = field(default_factory=list)  # {role, text, at}
    team_notes: list[str] = field(default_factory=list)  # notes from the latest draft/plan
    usage: dict[str, int] = field(default_factory=lambda: {"requests": 0, "input_tokens": 0, "output_tokens": 0})
    feed: list[dict] = field(default_factory=list)  # live team activity, memory only
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    # ---------------------------------------------------------------- helpers

    def say(self, role: str, text: str) -> None:
        self.transcript.append({"role": role, "text": text, "at": _now().isoformat(timespec="seconds")})

    def post(self, kind: str, agent: str, text: str, to: str | None = None) -> None:
        """Add a line to the live team feed (shown in the huddle window)."""
        seq = (self.feed[-1]["seq"] + 1) if self.feed else 1
        self.feed.append({"seq": seq, "at": _now().isoformat(timespec="seconds"), "kind": kind,
                          "agent": agent, "to": to, "text": text[:600]})
        del self.feed[:-FEED_LIMIT]

    def add_usage(self, usage: dict[str, int]) -> None:
        for k in self.usage:
            self.usage[k] += usage.get(k, 0)

    @property
    def current_draft(self) -> LogicModel | None:
        return LogicModel.model_validate(self.drafts[-1]["logic_model"]) if self.drafts else None

    @property
    def current_plan(self) -> MeasurementPlan | None:
        return MeasurementPlan.model_validate(self.metric_drafts[-1]["plan"]) if self.metric_drafts else None

    @property
    def answered(self) -> int:
        return sum(1 for q in self.questions if q.get("answer"))

    def interview_text(self) -> str:
        if not self.questions:
            return "(No interview questions yet.)"
        lines = []
        for q in self.questions:
            lines.append(f"Q{q['number']}: {q['question']}")
            lines.append(f"A{q['number']}: {q.get('answer') or '(not answered yet)'}")
        if self.notes:
            lines.append("\nTeam notes:\n" + "\n".join(f"- {n}" for n in self.notes))
        return "\n".join(lines)

    def wipe_working_notes(self) -> None:
        """Forget everything derived from the client's uploads."""
        self.source_text = None
        self.pending_sources = []
        self.snapshot = None
        self.sector_brief = None
        self.field_research = None
        self.metrics_research = None
        self.question_pool = []
        self.notes = []

    # ---------------------------------------------------------------- views

    def research_view(self) -> dict | None:
        """What the client sees of the field research: who funders are and the sources (no client data)."""
        r = self.field_research
        if not r:
            return None
        return {
            "mode": self.research_mode,
            "funder_priorities": [f.model_dump() for f in r.funder_priorities],
            "compelling_metrics": r.compelling_metrics,
            "sources": [c.model_dump() for c in r.sources],
        }

    def view(self) -> dict:
        """Everything the frontend needs. Never includes uploaded source text."""
        open_q = next((q for q in self.questions if not q.get("answer")), None)
        return {
            "session_id": self.id,
            "org_name": self.org_name,
            "phase": self.phase,
            "sources": self.source_manifest,
            "sector": self.snapshot.sector if self.snapshot else None,
            "question_number": open_q["number"] if open_q else None,
            "questions_total": INTERVIEW_QUESTIONS,
            "answered": self.answered,
            "current_question": open_q,
            "transcript": self.transcript,
            "draft": self.drafts[-1] if self.drafts else None,
            "revisions_left": MAX_REVISIONS - self.revisions_used,
            "approved": self.approved.model_dump() if self.approved else None,
            "metric_draft": self.metric_drafts[-1] if self.metric_drafts else None,
            "metric_revisions_left": MAX_METRIC_REVISIONS - self.metric_revisions_used,
            "approved_plan": self.approved_plan.model_dump() if self.approved_plan else None,
            "upload_request": self.upload_request if self.extra_uploads < MAX_EXTRA_UPLOADS else None,
            "uploads_left": MAX_EXTRA_UPLOADS - self.extra_uploads,
            "team_notes": self.team_notes,
            "research": self.research_view(),
            "usage": self.usage,
            "feed_seq": self.feed[-1]["seq"] if self.feed else 0,
        }

    def record(self) -> dict:
        data = {
            "session_id": self.id,
            "org_name": self.org_name,
            "org_id": self.org_id,
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "last_active": self.last_active.isoformat(timespec="seconds"),
            "phase": self.phase,
            "ended": self.ended,
            "sources": self.source_manifest,  # kinds and sizes only
            "questions": self.questions,
            "transcript": self.transcript,
            "drafts": self.drafts,
            "revisions_used": self.revisions_used,
            "approved_logic_model": self.approved.model_dump() if self.approved else None,
            "metric_drafts": self.metric_drafts,
            "metric_revisions_used": self.metric_revisions_used,
            "approved_plan": self.approved_plan.model_dump() if self.approved_plan else None,
            "upload_request": self.upload_request,
            "extra_uploads": self.extra_uploads,
            "team_notes": self.team_notes,
            "usage": self.usage,
        }
        # Working notes ride along only while the session is active (restart safety).
        if not self.ended and self.phase != "complete":
            data["working_notes"] = {
                "snapshot": self.snapshot.model_dump() if self.snapshot else None,
                "sector_brief": self.sector_brief.model_dump() if self.sector_brief else None,
                "field_research": self.field_research.model_dump() if self.field_research else None,
                "metrics_research": self.metrics_research.model_dump() if self.metrics_research else None,
                "research_mode": self.research_mode,
                "question_pool": self.question_pool,
                "notes": self.notes,
            }
        return data

    def save(self) -> None:
        path = sessions_dir() / f"{self.id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.record(), indent=2), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def from_record(cls, data: dict) -> "Session":
        working = data.get("working_notes") or {}
        return cls(
            id=data["session_id"], org_name=data["org_name"], org_id=data.get("org_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data.get("last_active", data["created_at"])),
            phase={"approved": "ready_for_metrics"}.get(data["phase"], data["phase"]),  # pre-metrics records
            ended=data.get("ended", False),
            source_manifest=data.get("sources", []),
            snapshot=OrgSnapshot.model_validate(working["snapshot"]) if working.get("snapshot") else None,
            sector_brief=SectorBrief.model_validate(working["sector_brief"]) if working.get("sector_brief") else None,
            field_research=FieldResearch.model_validate(working["field_research"]) if working.get("field_research") else None,
            metrics_research=(MetricsResearch.model_validate(working["metrics_research"])
                              if working.get("metrics_research") else None),
            research_mode=working.get("research_mode"),
            question_pool=working.get("question_pool", []),
            notes=working.get("notes", []),
            questions=data.get("questions", []), drafts=data.get("drafts", []),
            revisions_used=data.get("revisions_used", 0),
            approved=LogicModel.model_validate(data["approved_logic_model"]) if data.get("approved_logic_model") else None,
            metric_drafts=data.get("metric_drafts", []),
            metric_revisions_used=data.get("metric_revisions_used", 0),
            approved_plan=MeasurementPlan.model_validate(data["approved_plan"]) if data.get("approved_plan") else None,
            upload_request=data.get("upload_request"), extra_uploads=data.get("extra_uploads", 0),
            transcript=data.get("transcript", []), team_notes=data.get("team_notes", []),
            usage=data.get("usage") or {"requests": 0, "input_tokens": 0, "output_tokens": 0},
        )


# ============================================================ the store

_SESSIONS: dict[str, Session] = {}


def _expire(session: Session) -> None:
    session.ended = True
    session.wipe_working_notes()
    session.save()
    _SESSIONS.pop(session.id, None)


def _purge_idle() -> None:
    cutoff = _now() - SESSION_LIFETIME
    for s in [s for s in _SESSIONS.values() if s.last_active < cutoff]:
        if s.phase == "complete":
            _SESSIONS.pop(s.id, None)  # finished work stays viewable; it just leaves memory (notes were wiped at completion)
        else:
            _expire(s)


def create(org_name: str, org_id: int | None = None) -> Session:
    _purge_idle()
    session = Session(id="ses-" + secrets.token_urlsafe(12), org_name=org_name.strip()[:120], org_id=org_id)
    _SESSIONS[session.id] = session
    session.save()
    return session


def get(session_id: str) -> Session | None:
    """Find a live session in memory, or reload it from disk after a server restart."""
    _purge_idle()
    session = _SESSIONS.get(session_id)
    if session is None:
        path = sessions_dir() / f"{session_id}.json"
        if not session_id.startswith("ses-") or "/" in session_id or "\\" in session_id or not path.exists():
            return None
        session = Session.from_record(json.loads(path.read_text(encoding="utf-8")))
        if session.ended:
            return None
        if session.last_active < _now() - SESSION_LIFETIME and session.phase != "complete":
            _expire(session)
            return None
        _SESSIONS[session.id] = session
    session.last_active = _now()
    return session


def end(session_id: str) -> bool:
    """End the session: wipe working notes from memory and disk. The record of what was typed stays."""
    session = get(session_id)
    if not session:
        return False
    _expire(session)
    return True
