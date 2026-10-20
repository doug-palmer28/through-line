"""The token ledger: every agent run's tokens, attributed to an organization and a staff member.

`run_agent` (agents/common.py) records one row per run, including runs that fail or hit
a cap, because those tokens were still used. Staff see their own and their
organization's totals at GET /api/usage; the operator gets every organization from
`scripts/operator_tools.py usage`.
"""

from collections import defaultdict

from sqlmodel import Session, select

from db import Organization, StaffUser, TokenUsage, engine

EARLIER = "(before per-person tracking)"
FEATURES = {"studio": "Logic Model Studio", "survey_review": "Survey Review Bot",
            "impact_report": "Impact report", "grants": "Grant applications"}


def _person(names: dict, user_id: int | None) -> str:
    return names.get(user_id) or (EARLIER if user_id is None else "Former staff")


def record(*, org_id: int | None, user_id: int | None, feature: str, phase: str, agent: str, run_id: str,
           usage: dict, ok: bool = True) -> None:
    if org_id is None:
        return  # not tied to an organization (offline unit tests of single agents)
    with Session(engine()) as db:
        db.add(TokenUsage(org_id=org_id, user_id=user_id, feature=feature, phase=phase, agent=agent, run_id=run_id,
                          requests=usage.get("requests", 0), input_tokens=usage.get("input_tokens", 0),
                          output_tokens=usage.get("output_tokens", 0), web_searches=usage.get("web_searches", 0),
                          ok=ok))
        db.commit()


def _totals(rows) -> dict:
    t = {"requests": 0, "input_tokens": 0, "output_tokens": 0}
    for r in rows:
        t["requests"] += r.requests
        t["input_tokens"] += r.input_tokens
        t["output_tokens"] += r.output_tokens
    t["total_tokens"] = t["input_tokens"] + t["output_tokens"]
    return t


def _grouped(rows, key) -> list[dict]:
    groups = defaultdict(list)
    for r in rows:
        groups[key(r)].append(r)
    return [{"key": k, **_totals(v)} for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))]


def org_report(db: Session, org_id: int, user_id: int, include_people: bool) -> dict:
    rows = db.exec(select(TokenUsage).where(TokenUsage.org_id == org_id)).all()
    mine = [r for r in rows if r.user_id == user_id]
    report = {
        "me": {**_totals(mine), "by_feature": _grouped(mine, lambda r: FEATURES.get(r.feature, r.feature))},
        "organization": {**_totals(rows),
                         "by_feature": _grouped(rows, lambda r: FEATURES.get(r.feature, r.feature)),
                         "by_month": _grouped(rows, lambda r: r.at.strftime("%Y-%m"))},
    }
    if include_people:
        staff = db.exec(select(StaffUser).where(StaffUser.org_id == org_id)).all()
        dupes = {n for n in (u.display_name for u in staff) if sum(s.display_name == n for s in staff) > 1}
        names = {u.id: u.display_name + (f" (#{u.id})" if u.display_name in dupes else "") for u in staff}
        report["organization"]["by_person"] = _grouped(rows, lambda r: _person(names, r.user_id))
    return report


def platform_rows(db: Session) -> list[dict]:
    """Every run, with organization and staff names, for the operator report."""
    orgs = {o.id: o.name for o in db.exec(select(Organization)).all()}
    users = {u.id: u.display_name for u in db.exec(select(StaffUser)).all()}
    return [{"when": r.at.strftime("%Y-%m-%d %H:%M"), "organization": orgs.get(r.org_id, f"org {r.org_id}"),
             "org_id": r.org_id, "person": _person(users, r.user_id), "user_id": r.user_id,
             "feature": FEATURES.get(r.feature, r.feature), "phase": r.phase, "agent": r.agent,
             "requests": r.requests, "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
             "total_tokens": r.input_tokens + r.output_tokens, "ok": r.ok}
            for r in db.exec(select(TokenUsage).order_by(TokenUsage.at)).all()]
