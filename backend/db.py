"""The database: organizations, staff, participants, survey tools, responses, and program numbers.

SQLite via SQLModel (data/through_line.db, git-ignored). Every org-owned table
has `org_id`, and every query in the routes filters on it: one organization
can never read another's data.

What's deliberately NOT stored:
  * participant names or contact details: participants are known only by a code;
  * plain-text usernames, passwords, or PINs: only salted/peppered hashes (security.py).
"""

import os
from datetime import date, datetime, timezone
from functools import cache
from typing import Any

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field, Session, SQLModel, create_engine

from config import PROJECT_DIR


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Organization(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=_now)
    studio_session_id: str | None = None  # current Logic Model Studio session
    logic_model: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # approved copy
    measurement_plan: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # approved copy
    invite_hash: str | None = None  # hash of the current staff invite code
    invite_expires: datetime | None = None
    brand: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # design standards for reports
    # How much of each limited AI feature has been used (see allowances.py), e.g.
    # {"studio_starts": 1, "report_designs": 1, "grants": {"2026-10": 2}}
    allowance_used: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class StaffUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    username_hash: str = Field(unique=True, index=True)  # HMAC of the username; the username itself isn't stored
    password_hash: str  # Argon2id
    display_name: str
    role: str = "admin"  # "admin" (created the org) or "staff" (joined with an invite)
    created_at: datetime = Field(default_factory=_now)
    last_login: datetime | None = None


class Participant(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("org_id", "code"),)
    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    code: str = Field(index=True)  # e.g. "HL-4821": the only identifier we keep
    pin_hash: str  # Argon2id
    active: bool = True
    created_at: datetime = Field(default_factory=_now)


class Instrument(SQLModel, table=True):
    """A survey tool: participant survey or staff assessment, asked pre and post."""

    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    name: str
    method: str  # "participant_survey" | "staff_assessment"
    when: str = ""
    status: str = "draft"  # draft -> published
    questions: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    demographics: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    review: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # last Survey Review Bot result
    review_count: int = 0  # Survey Review Bot runs on this tool (limited)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Response(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("instrument_id", "participant_id", "wave"),)
    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    instrument_id: int = Field(foreign_key="instrument.id", index=True)
    participant_id: int = Field(foreign_key="participant.id", index=True)
    wave: str  # "pre" | "post"
    answers: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    demographics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    entered_by: str  # "participant" | "staff"
    staff_id: int | None = None
    created_at: datetime = Field(default_factory=_now)


class Indicator(SQLModel, table=True):
    """A number the organization reports itself (program records): dollars spent, event attendance, ..."""

    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    name: str
    unit: str = ""
    description: str = ""
    source: str = "custom"  # "plan" (from a program_records metric) or "custom"


class IndicatorEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    indicator_id: int = Field(foreign_key="indicator.id", index=True)
    period: date  # first day of the month (or the event date)
    value: float
    note: str = ""
    staff_id: int | None = None
    created_at: datetime = Field(default_factory=_now)


class ReportRun(SQLModel, table=True):
    """The organization's report "shell": the Report Designer's story and design, with numbers as {{key}} tokens
    that are filled from the latest data on every view and download."""

    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    created_at: datetime = Field(default_factory=_now)
    request: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    draft: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    privacy: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    status: str = "done"
    revisions: int = 0  # feedback rounds used (limited)
    feedback: list[Any] = Field(default_factory=list, sa_column=Column(JSON))  # what staff asked for, in order


class GrantApplication(SQLModel, table=True):
    """A draft grant application for one foundation. Uploaded files are never stored: only what the agents
    produced from them (the foundation profile and the draft)."""

    id: int | None = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    created_by: int | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    foundation: str
    foundation_url: str = ""
    request: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))  # questions + notes staff typed
    sources: list[Any] = Field(default_factory=list, sa_column=Column(JSON))  # kinds, sizes, hidden-text counts
    profile: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # FoundationProfile
    research_mode: str = ""
    draft: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # GrantDraft (numbers as tokens)
    privacy: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    revisions: int = 0
    feedback: list[Any] = Field(default_factory=list, sa_column=Column(JSON))


class TokenUsage(SQLModel, table=True):
    """One agent run's token use, attributed to the organization and the staff member who started it."""

    id: int | None = Field(default=None, primary_key=True)
    at: datetime = Field(default_factory=_now, index=True)
    org_id: int | None = Field(default=None, index=True)
    user_id: int | None = Field(default=None, index=True)
    feature: str  # studio | survey_review | impact_report | grants
    phase: str = ""
    agent: str = ""
    run_id: str = ""
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    web_searches: int = 0  # built-in web search calls (billed per call)
    ok: bool = True  # False if the run failed or hit a limit (tokens were still used)


# Columns added after the first release, so older databases get them too (SQLite can't add them via create_all).
_ADDED_COLUMNS = {
    "organization": {"brand": "JSON", "allowance_used": "JSON"},
    "instrument": {"review_count": "INTEGER NOT NULL DEFAULT 0"},
    "reportrun": {"revisions": "INTEGER NOT NULL DEFAULT 0", "feedback": "JSON"},
    "tokenusage": {"web_searches": "INTEGER NOT NULL DEFAULT 0"},
}


def _migrate(engine) -> None:
    with engine.begin() as conn:
        for table, cols in _ADDED_COLUMNS.items():
            have = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            for col, kind in cols.items():
                if have and col not in have:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {kind}")


def db_url() -> str:
    path = os.getenv("THROUGH_LINE_DB") or str(PROJECT_DIR / "data" / "through_line.db")  # empty counts as unset
    return f"sqlite:///{path}"


@cache
def _engine(url: str):
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 15})
    SQLModel.metadata.create_all(engine)
    _migrate(engine)
    return engine


def engine():
    return _engine(db_url())


def get_db():
    """FastAPI dependency: one DB session per request."""
    with Session(engine()) as session:
        yield session
