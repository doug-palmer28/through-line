"""How often each organization can use the AI agents ("tokenomics", part 2).

Per-run caps (requests, tokens, tool calls) live next to each agent. These are the
per-organization allowances on top of them, so no one can run the bots endlessly:

| Feature                          | Allowance                                              |
|----------------------------------|--------------------------------------------------------|
| Logic Model Studio               | 2 starts per organization (the 2nd covers an expired   |
|                                  | or abandoned session); inside a session: 5 questions,  |
|                                  | 2 extra documents, 2 revision rounds per artifact      |
| Survey Review Bot                | 2 reviews per survey tool                              |
| Impact report (Report Designer)  | 1 design per organization + 1 feedback round. After    |
|                                  | that the report refreshes with new data for free.      |
| Grant applications               | 3 new applications per calendar month + 1 feedback     |
|                                  | round each                                             |
| Privacy check                    | Any time (re-checking an unchanged draft is free;     |
|                                  | ceiling of 25 on-demand checks per org per day)        |

The operator (Doug) can see usage and give an organization more with
`scripts/operator_tools.py` (it lowers the "used" count; nothing is deleted).
"""

import threading
from datetime import datetime, timezone

from fastapi import HTTPException

STUDIO_STARTS = 2
SURVEY_REVIEWS_PER_TOOL = 2
REPORT_DESIGNS = 1
REPORT_REVISIONS = 1
GRANTS_PER_MONTH = 3
GRANT_REVISIONS = 1
PRIVACY_CHECKS_PER_DAY = 25  # on-demand checks; unchanged drafts are answered from the last check for free


def this_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def used(org, key: str) -> int:
    u = org.allowance_used or {}
    if key == "grants":
        return int((u.get("grants") or {}).get(this_month(), 0))
    return int(u.get(key, 0))


def limit_of(key: str) -> int:
    return {"studio_starts": STUDIO_STARTS, "report_designs": REPORT_DESIGNS, "grants": GRANTS_PER_MONTH}[key]


def left(org, key: str) -> int:
    return max(0, limit_of(key) - used(org, key))


def spend(org, key: str, message: str) -> None:
    """Use one of the organization's allowance, or refuse with 429 and a plain explanation.

    The caller commits the change together with its own work.
    """
    if left(org, key) <= 0:
        raise HTTPException(429, message)
    u = dict(org.allowance_used or {})
    if key == "grants":
        months = dict(u.get("grants") or {})
        months[this_month()] = months.get(this_month(), 0) + 1
        u["grants"] = months
    else:
        u[key] = u.get(key, 0) + 1
    org.allowance_used = u  # reassign so SQLAlchemy sees the JSON change


def refund(org, key: str) -> None:
    """Give one back (the AI run failed, so the organization shouldn't lose its turn)."""
    u = dict(org.allowance_used or {})
    if key == "grants":
        months = dict(u.get("grants") or {})
        months[this_month()] = max(0, months.get(this_month(), 0) - 1)
        u["grants"] = months
    else:
        u[key] = max(0, u.get(key, 0) - 1)
    org.allowance_used = u


# ============================================================ claiming (race-safe)
#
# Two quick clicks must not both get the last allowance. The app runs as ONE server process
# (see Dockerfile), so a process lock around "re-read, check, count, commit" is enough. The claim is
# committed before the AI run (never hold a database write open for minutes) and released if it fails.

_LOCK = threading.Lock()


def claim(db, org, key: str, message: str) -> None:
    with _LOCK:
        db.refresh(org)
        spend(org, key, message)
        db.add(org)
        db.commit()


def release(db, org, key: str) -> None:
    with _LOCK:
        db.refresh(org)
        refund(org, key)
        db.add(org)
        db.commit()


def claim_count(db, row, field: str, limit: int, message: str) -> None:
    """Same idea for per-item counters (revision rounds, survey reviews)."""
    with _LOCK:
        db.refresh(row)
        if (getattr(row, field) or 0) >= limit:
            raise HTTPException(429, message)
        setattr(row, field, (getattr(row, field) or 0) + 1)
        db.add(row)
        db.commit()


def release_count(db, row, field: str) -> None:
    with _LOCK:
        db.refresh(row)
        setattr(row, field, max(0, (getattr(row, field) or 0) - 1))
        db.add(row)
        db.commit()


def check_privacy_allowed(db, org_id: int) -> None:
    """The privacy check is 'any time' for people, but not unlimited for scripts: a daily ceiling."""
    from datetime import timedelta

    from sqlmodel import func, select

    from db import TokenUsage

    since = datetime.now(timezone.utc) - timedelta(days=1)
    n = db.exec(select(func.count()).select_from(TokenUsage).where(
        TokenUsage.org_id == org_id, TokenUsage.agent == "privacy_reviewer", TokenUsage.phase == "privacy_check",
        TokenUsage.at >= since)).one()
    if n >= PRIVACY_CHECKS_PER_DAY:
        raise HTTPException(429, f"That's {PRIVACY_CHECKS_PER_DAY} privacy checks in the last day. Please try again tomorrow.")


def summary(org) -> list[dict]:
    """What staff see on the usage page."""
    return [
        {"feature": "Logic Model Studio sessions", "used": used(org, "studio_starts"), "limit": STUDIO_STARTS,
         "per": "organization"},
        {"feature": "Impact report designs", "used": used(org, "report_designs"), "limit": REPORT_DESIGNS,
         "per": "organization", "note": f"{REPORT_REVISIONS} feedback round; refreshing with new data is free"},
        {"feature": "New grant applications", "used": used(org, "grants"), "limit": GRANTS_PER_MONTH,
         "per": "month", "note": f"{GRANT_REVISIONS} feedback round each"},
        {"feature": "Survey Review Bot", "used": None, "limit": SURVEY_REVIEWS_PER_TOOL, "per": "survey tool"},
        {"feature": "Privacy check", "used": None, "limit": None, "per": "any time",
         "note": f"re-checking an unchanged draft is free; up to {PRIVACY_CHECKS_PER_DAY} new checks a day"},
    ]
