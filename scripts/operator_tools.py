"""Operator tools for whoever runs Through Line: token usage across every organization, and allowances.

    .venv/Scripts/python scripts/operator_tools.py usage               # print totals + write an Excel report
    .venv/Scripts/python scripts/operator_tools.py orgs                # organizations and what they've used
    .venv/Scripts/python scripts/operator_tools.py backfill            # once: copy pre-ledger usage from the audit log
    .venv/Scripts/python scripts/operator_tools.py allow 1 grants      # give org 1 one more grant this month
    .venv/Scripts/python scripts/operator_tools.py allow 1 report-revision --item 3

Allowance kinds: studio, report, grants, report-revision (--item report id),
grant-revision (--item application id), survey-review (--item survey tool id).
"allow" lowers the used count by one (or --n); it never deletes anything, and it's audited.

Reads the real database (data/through_line.db) unless THROUGH_LINE_DB is set. The Excel
report goes to data/usage_reports/ (git-ignored): it names staff and organizations.
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Font, PatternFill  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

import allowances  # noqa: E402
import ledger  # noqa: E402
from audit import audit_append  # noqa: E402
from db import GrantApplication, Instrument, Organization, ReportRun, engine  # noqa: E402
from reports import excel_safe  # noqa: E402

NUMS = ("requests", "input_tokens", "output_tokens", "total_tokens")


def _sum(rows, key) -> list[tuple]:
    groups: dict = defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        g = groups[key(r)]
        for i, n in enumerate(NUMS):
            g[i] += r[n]
    return [(*(k if isinstance(k, tuple) else (k,)), *v) for k, v in sorted(groups.items())]


def _sheet(wb, title: str, header: list[str], rows) -> None:
    ws = wb.create_sheet(title)
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="23262B")
    for row in rows:
        ws.append([excel_safe(v) for v in row])  # org and staff names are user-typed: never formulas
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = max(12, min(40, max(len(str(c.value or "")) for c in col) + 2))
    ws.freeze_panes = "A2"


def usage_report(out_dir: Path | None = None) -> Path:
    with Session(engine()) as db:
        rows = ledger.platform_rows(db)
    wb = Workbook()
    wb.remove(wb.active)
    totals = ["Requests", "Input tokens", "Output tokens", "Total tokens"]
    _sheet(wb, "By organization", ["Organization", *totals], _sum(rows, lambda r: r["organization"]))
    _sheet(wb, "By person", ["Organization", "Person", *totals], _sum(rows, lambda r: (r["organization"], r["person"])))
    _sheet(wb, "By feature", ["Organization", "Feature", *totals], _sum(rows, lambda r: (r["organization"], r["feature"])))
    _sheet(wb, "By month", ["Month", "Organization", *totals], _sum(rows, lambda r: (r["when"][:7], r["organization"])))
    _sheet(wb, "Every run", list(rows[0].keys()) if rows else ["(no runs yet)"], [list(r.values()) for r in rows])
    out_dir = out_dir or ROOT / "data" / "usage_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"usage_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    wb.save(path)
    return path


def _feature_of(phase: str) -> str:
    if phase == "survey_review":
        return "survey_review"
    if phase.startswith("report") or phase == "privacy_check":
        return "impact_report"
    if phase.startswith("grant"):
        return "grants"
    return "studio"


def backfill() -> str:
    """Copy token use recorded in the audit log before the ledger existed (person unknown). Safe to re-run."""
    import json
    import os
    import re

    from config import AUDIT_LOG_PATH
    from db import TokenUsage

    log = json.loads(Path(os.getenv("THROUGH_LINE_AUDIT", AUDIT_LOG_PATH)).read_text(encoding="utf-8"))
    sessions_dir = ROOT / "data" / "sessions"
    org_of_session: dict[str, int | None] = {}

    def org_for(session_id: str | None) -> int | None:
        if not session_id:
            return None
        m = re.match(r"org-(\d+)-", session_id)
        if m:
            return int(m.group(1))
        if session_id not in org_of_session:
            path = sessions_dir / f"{session_id}.json"
            org_of_session[session_id] = json.loads(path.read_text(encoding="utf-8")).get("org_id") if path.exists() else None
        return org_of_session[session_id]

    added = skipped = 0
    with Session(engine()) as db:
        done = {r.run_id for r in db.exec(select(TokenUsage).where(TokenUsage.run_id.startswith("audit:"))).all()}
        first_live = min((r.at for r in db.exec(select(TokenUsage).where(~TokenUsage.run_id.startswith("audit:"))).all()),
                         default=None)
        for e in log:
            if e.get("event") not in ("agent_finished", "agent_failed", "limit_reached") or not e.get("usage"):
                continue
            key = f"audit:{e['seq']}"
            at = datetime.fromisoformat(e["logged_at"])
            if key in done or (first_live and at.replace(tzinfo=None) >= first_live.replace(tzinfo=None)):
                continue  # already copied, or already recorded live by the ledger
            org_id = org_for(e.get("session_id"))
            if org_id is None:
                skipped += 1
                continue
            u = e["usage"]
            db.add(TokenUsage(at=at, org_id=org_id, user_id=None, feature=_feature_of(e.get("phase") or ""),
                              phase=e.get("phase") or "", agent=e.get("agent") or "", run_id=key,
                              requests=u.get("requests", 0), input_tokens=u.get("input_tokens", 0),
                              output_tokens=u.get("output_tokens", 0), ok=e["event"] == "agent_finished"))
            added += 1
        db.commit()
    return f"Copied {added} earlier agent runs from the audit log ({skipped} had no organization, e.g. pre-accounts tests)."


def print_usage() -> None:
    with Session(engine()) as db:
        rows = ledger.platform_rows(db)
    print(f"{'Organization':34} {'Person':24} {'Requests':>9} {'Input':>11} {'Output':>10} {'Total':>11}")
    for org, person, req, inp, outp, tot in _sum(rows, lambda r: (r["organization"], r["person"])):
        print(f"{org[:34]:34} {person[:24]:24} {req:9,} {inp:11,} {outp:10,} {tot:11,}")
    grand = sum(r["total_tokens"] for r in rows)
    print(f"\n{len(rows)} agent runs, {grand:,} tokens in total.")


def print_orgs() -> None:
    with Session(engine()) as db:
        for org in db.exec(select(Organization)).all():
            parts = [f"{a['feature']}: {a['used']}/{a['limit']}" for a in allowances.summary(org) if a["used"] is not None]
            print(f"[{org.id}] {org.name}: " + "; ".join(parts))


def allow(org_id: int, kind: str, item: int | None, n: int) -> str:
    with Session(engine()) as db:
        org = db.get(Organization, org_id)
        if not org:
            raise SystemExit(f"No organization {org_id}.")
        if kind in ("studio", "report", "grants"):
            key = {"studio": "studio_starts", "report": "report_designs", "grants": "grants"}[kind]
            for _ in range(n):
                allowances.refund(org, key)
            db.add(org)
        else:
            model, field = {"report-revision": (ReportRun, "revisions"), "grant-revision": (GrantApplication, "revisions"),
                            "survey-review": (Instrument, "review_count")}[kind]
            row = db.get(model, item) if item else None
            if not row or row.org_id != org_id:
                raise SystemExit(f"No {kind.split('-')[0]} {item} for organization {org_id} (use --item).")
            setattr(row, field, max(0, (getattr(row, field) or 0) - n))
            db.add(row)
        db.commit()
        audit_append(event="operator_allowance", agent="human", team="operator",
                     human={"role": "operator", "action": f"allowed {n} more {kind}", "org_id": org_id},
                     output={"item": item})
        return f"Organization {org_id} ({org.name}) can use {n} more {kind}."


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("usage", help="token totals by organization and person, plus an Excel report")
    sub.add_parser("orgs", help="organizations and their allowance use")
    sub.add_parser("backfill", help="copy token use from the audit log for runs before the ledger existed")
    p = sub.add_parser("allow", help="give an organization more of a limited feature")
    p.add_argument("org_id", type=int)
    p.add_argument("kind", choices=["studio", "report", "grants", "report-revision", "grant-revision", "survey-review"])
    p.add_argument("--item", type=int, default=None)
    p.add_argument("--n", type=int, default=1)
    args = ap.parse_args()
    if args.cmd == "usage":
        print_usage()
        print(f"Excel report: {usage_report()}")
    elif args.cmd == "orgs":
        print_orgs()
    elif args.cmd == "backfill":
        print(backfill())
    else:
        print(allow(args.org_id, args.kind, args.item, args.n))
