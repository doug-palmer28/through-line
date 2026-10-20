"""Dashboard: charts and numbers from incoming survey data and program numbers, plus downloads."""

import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

import design
import reports
from audit import audit_append
from branding import load_logo
from deps import StaffCtx, current_staff

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")[:50] or "chart"


def _file(data: bytes, media: str, name: str) -> Response:
    return Response(content=data, media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'})


def _exported(ctx: StaffCtx, what: str) -> None:
    audit_append(event="data_exported", agent="human", team="reporting",
                 human={"role": "staff", "action": f"downloaded_{what}", "org_id": ctx.org.id})


@router.get("")
def dashboard(ctx: StaffCtx = Depends(current_staff)):
    return reports.compute(ctx.db, ctx.org)


@router.get("/charts/{chart_id}.xlsx")
def chart_excel(chart_id: str, ctx: StaffCtx = Depends(current_staff)):
    chart = next((c for c in reports.compute(ctx.db, ctx.org)["charts"] if c["id"] == chart_id), None)
    if not chart:
        raise HTTPException(404, "That chart isn't available.")
    _exported(ctx, f"chart_{chart_id}")
    return _file(reports.chart_xlsx(chart), XLSX, f"{_slug(chart['title'])}.xlsx")


@router.get("/data.xlsx")
def data_excel(ctx: StaffCtx = Depends(current_staff)):
    _exported(ctx, "all_data")
    return _file(reports.data_xlsx(ctx.db, ctx.org), XLSX, f"{_slug(ctx.org.name)}_survey_data.xlsx")


@router.get("/report.pptx")
def report(ctx: StaffCtx = Depends(current_staff)):
    _exported(ctx, "impact_report")
    # The org's saved brand (if any) styles the quick report too.
    theme = design.theme_from(None, ctx.org.brand, ctx.org.name, load_logo(ctx.org.id)) if ctx.org.brand else None
    data = design.quick_report_pptx(reports.compute(ctx.db, ctx.org), ctx.org.name, ctx.org.logic_model, theme)
    return _file(data, PPTX, f"{_slug(ctx.org.name)}_impact_report.pptx")
