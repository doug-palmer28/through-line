"""Designed outputs: the quick impact report, the Report Designer's funder deck, and the one-page flyer.

Everything renders from data already computed by reports.compute() and (for the funder deck and flyer)
the Report Designer's plan. Charts in PowerPoint are native and editable, styled per chart type:

  before/after  -> two columns, "before" in a quiet gray, "after" in the brand color, big labels, no axis
  percentages   -> horizontal bars on a 0-100 scale, direct labels, no gridlines
  comparisons   -> clustered columns with a legend
  monthly       -> a 2.25pt line with markers and short month labels

Text color always comes from the theme's ink, never the series color.
"""

import io
import os
import re
import textwrap
from dataclasses import dataclass, field
from functools import cache
from datetime import date, datetime
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

import reports

# ============================================================ theme


@dataclass
class Theme:
    primary: str = "#3E63B0"
    secondary: str = "#D96C4F"
    accent: str = "#E8B84A"
    background: str = "#FFFFFF"
    ink: str = "#23262B"
    muted: str = "#6B6F76"
    quiet: str = "#C9CDD3"  # the "before" bars and hairlines
    tint: str = "#F3F5F8"  # card backgrounds
    heading_font: str = "Century Gothic"
    body_font: str = "Segoe UI"
    logo: bytes | None = None
    org_name: str = ""
    tagline: str = ""
    contact: str = ""
    extra: dict = field(default_factory=dict)


HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")
SAFE_FONTS = ["Georgia", "Calibri", "Arial", "Segoe UI", "Century Gothic", "Garamond", "Trebuchet MS", "Verdana"]


def _hex(value: str | None, fallback: str) -> str:
    return ("#" + value.lstrip("#").upper()) if value and HEX.match(value.strip()) else fallback


def _rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.lstrip("#").upper())


def _blend(hex_color: str, with_hex: str = "#FFFFFF", amount: float = 0.88) -> str:
    amount = min(1.0, max(0.0, amount))
    a, b = hex_color.lstrip("#"), with_hex.lstrip("#")
    mix = [min(255, max(0, round(int(a[i:i + 2], 16) * (1 - amount) + int(b[i:i + 2], 16) * amount))) for i in (0, 2, 4)]
    return "#" + "".join(f"{v:02X}" for v in mix)


def theme_from(design: dict | None, brand: dict | None, org_name: str, logo: bytes | None) -> Theme:
    d, b = design or {}, brand or {}
    primary = _hex(b.get("primary") or d.get("primary"), "#3E63B0")
    t = Theme(
        primary=primary,
        secondary=_hex(b.get("secondary") or d.get("secondary"), "#D96C4F"),
        accent=_hex(b.get("accent") or d.get("accent"), "#E8B84A"),
        background=_hex(d.get("background"), "#FFFFFF"),
        heading_font=next((f for f in SAFE_FONTS if f == (b.get("heading_font") or d.get("heading_font"))), "Georgia"),
        body_font=next((f for f in SAFE_FONTS if f == (b.get("body_font") or d.get("body_font"))), "Calibri"),
        logo=logo, org_name=org_name, tagline=b.get("tagline", ""), contact=b.get("contact", ""),
    )
    t.tint = _blend(primary, "#FFFFFF", 0.92)
    return t


# ============================================================ small helpers


def short_month(ym: str) -> str:
    try:
        return datetime.strptime(ym, "%Y-%m").strftime("%b %y")
    except ValueError:
        return ym


def short(text: str, n: int = 48) -> str:
    """Trim to n characters at a word boundary."""
    if len(text) <= n:
        return text
    cut = text[: n - 1].rsplit(" ", 1)[0] if " " in text[: n - 1] else text[: n - 1]
    return cut.rstrip(" ,;:-") + "…"


def wrap2(text: str, width: int) -> str:
    """Up to two lines for a chart category label."""
    lines = textwrap.wrap(text, width)
    return "\n".join(lines[:1] + [short(" ".join(lines[1:]), width)]) if len(lines) > 1 else text


def fmt_value(v: float | None, unit: str) -> str:
    if v is None:
        return "–"
    if unit == "%":
        return f"{v:.0f}%"
    if unit == "$":
        return f"${v:,.0f}"
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"


def chart_kind(chart: dict) -> str:
    if chart["kind"] == "line":
        return "line"
    if chart["categories"] == ["Before (pre)", "After (post)"]:
        return "before_after"
    if len(chart["series"]) > 1:
        return "compare"
    return "bars"


# ============================================================ PowerPoint primitives


def _text(slide, x, y, w, h, lines, theme: Theme, size=16, bold=False, color=None, font=None,
          align=None, anchor=None, space=6, italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    if anchor:
        tf.vertical_anchor = anchor
    for i, line in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        runs = line if isinstance(line, list) else [(line, bold)]
        for t, b in runs:
            r = p.add_run()
            r.text = t
            r.font.size, r.font.bold, r.font.italic = Pt(size), b, italic
            r.font.name = font or theme.body_font
            r.font.color.rgb = _rgb(color or theme.ink)
        p.space_after = Pt(space)
        if align is not None:
            p.alignment = align
    return box


def _rect(slide, x, y, w, h, fill: str, kind=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = _rgb(fill)
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def _logo(slide, theme: Theme, x, y, h):
    if theme.logo:
        slide.shapes.add_picture(io.BytesIO(theme.logo), Inches(x), Inches(y), height=Inches(h))


def _new_slide(prs, theme: Theme, notes: str = ""):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = _rgb(theme.background)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def _page(prs, theme: Theme, headline: str, kicker: str = "", notes: str = ""):
    """A content slide: thin brand rule, kicker, headline, footer with org name, page number and small logo."""
    s = _new_slide(prs, theme, notes)
    _rect(s, 0.6, 0.55, 0.9, 0.07, theme.primary)
    if kicker:
        _text(s, 0.6, 0.7, 9, 0.35, kicker.upper(), theme, 10.5, True, theme.muted)
    _text(s, 0.6, 1.0, 11.6, 1.0, headline, theme, 28, True, font=theme.heading_font, space=0)
    _text(s, 0.6, 7.0, 8, 0.3, theme.org_name, theme, 9.5, False, theme.muted)
    _text(s, 11.9, 7.0, 0.8, 0.3, str(len(prs.slides)), theme, 9.5, False, theme.muted, align=PP_ALIGN.RIGHT)
    _logo(s, theme, 12.05, 0.45, 0.5)
    return s


def _style_axis_text(axis, theme: Theme, size=12):
    axis.tick_labels.font.size = Pt(size)
    axis.tick_labels.font.name = theme.body_font
    axis.tick_labels.font.color.rgb = _rgb(theme.ink)


def add_chart(slide, chart: dict, x, y, w, h, theme: Theme, title: str | None = None):
    """A native, editable chart styled for its kind. Returns the chart object."""
    kind = chart_kind(chart)
    unit = chart.get("unit", "")
    pct = unit == "%" or unit.startswith("%")
    cd = CategoryChartData()
    cats = chart["categories"]
    if kind == "line":
        cats = [short_month(c) for c in cats]
    elif kind == "before_after":
        cats = ["Before", "After"]
    else:
        cats = [short(c, 42) for c in cats]
    cd.categories = cats
    for ser in chart["series"]:
        cd.add_series(ser["name"], [v if v is not None else 0 for v in ser["values"]])

    xl = {"line": XL_CHART_TYPE.LINE_MARKERS, "before_after": XL_CHART_TYPE.COLUMN_CLUSTERED,
          "compare": XL_CHART_TYPE.COLUMN_CLUSTERED, "bars": XL_CHART_TYPE.BAR_CLUSTERED}[kind]
    gf = slide.shapes.add_chart(xl, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    c = gf.chart
    c.font.name, c.font.size = theme.body_font, Pt(12)
    c.font.color.rgb = _rgb(theme.ink)
    c.has_title = bool(title)
    if title:
        c.chart_title.text_frame.text = title
        for p in c.chart_title.text_frame.paragraphs:
            for r in p.runs:
                r.font.size, r.font.bold, r.font.name = Pt(14), True, theme.heading_font
                r.font.color.rgb = _rgb(theme.ink)
    c.has_legend = kind == "compare"
    if c.has_legend:
        c.legend.position, c.legend.include_in_layout = XL_LEGEND_POSITION.TOP, False
        c.legend.font.size, c.legend.font.name = Pt(11), theme.body_font

    plot = c.plots[0]
    va, ca = c.value_axis, c.category_axis
    va.minimum_scale = 0
    if pct:  # bar labels sit outside the bar end, so leave them room past 100%
        va.maximum_scale = 100 if kind == "line" else 118
    ca.format.line.color.rgb = _rgb(theme.quiet)
    _style_axis_text(ca, theme, 12 if kind != "line" else 11)
    ca.has_major_gridlines = False

    whole = all(float(v).is_integer() for s in chart["series"] for v in s["values"] if v is not None)
    number_format = '0"%"' if pct else ('$#,##0' if unit == "$" else ('#,##0' if whole else '#,##0.00'))
    if kind == "line":
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = _rgb(_blend(theme.quiet, "#FFFFFF", 0.5))
        va.format.line.fill.background()
        _style_axis_text(va, theme, 10)
        va.tick_labels.number_format, va.tick_labels.number_format_is_linked = number_format, False
        ser = plot.series[0]
        ser.format.line.color.rgb = _rgb(theme.primary)
        ser.format.line.width = Pt(2.25)
        ser.smooth = False
        ser.marker.size = 7
        ser.marker.format.fill.solid()
        ser.marker.format.fill.fore_color.rgb = _rgb(theme.primary)
        ser.marker.format.line.color.rgb = _rgb("#FFFFFF")
        # Label only the latest month, written out so it carries the unit ($38,100 rather than 38100).
        lbl = ser.points[len(chart["categories"]) - 1].data_label
        lbl.position = XL_LABEL_POSITION.ABOVE
        lbl.text_frame.text = fmt_value(chart["series"][0]["values"][-1], unit)
        run = lbl.text_frame.paragraphs[0].runs[0]
        run.font.size, run.font.bold, run.font.name = Pt(12), True, theme.body_font
        run.font.color.rgb = _rgb(theme.ink)
        return c

    # bar-type charts: no gridlines, no value axis, direct labels
    va.has_major_gridlines = False
    va.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    va.format.line.fill.background()
    plot.gap_width = 70 if kind == "bars" else 90
    plot.overlap = -10 if kind == "compare" else 0
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.font.size, dl.font.bold, dl.font.name = Pt(13 if kind == "before_after" else 12), True, theme.body_font
    dl.font.color.rgb = _rgb(theme.ink)
    dl.number_format, dl.number_format_is_linked = number_format, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    if kind == "bars":
        ca.reverse_order = True
    for i, ser in enumerate(plot.series):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = _rgb(theme.primary if i == len(plot.series) - 1 else theme.quiet)
        if kind == "compare" and i == 0:
            ser.format.fill.fore_color.rgb = _rgb(_blend(theme.primary, "#FFFFFF", 0.55))
    if kind == "before_after":
        before = plot.series[0].points[0]
        before.format.fill.solid()
        before.format.fill.fore_color.rgb = _rgb(theme.quiet)
    return c


# ============================================================ slide layouts (shared by both decks)


def slide_cover(prs, theme: Theme, title: str, subtitle: str, notes: str = ""):
    s = _new_slide(prs, theme, notes)
    _rect(s, 0, 0, 5.2, 7.5, theme.primary)
    _rect(s, 5.2, 0, 0.12, 7.5, theme.accent)
    if theme.logo:
        _rect(s, 0.6, 0.6, 1.5, 1.5, "#FFFFFF", MSO_SHAPE.OVAL)
        _logo(s, theme, 0.78, 0.78, 1.14)
    _text(s, 0.6, 5.6, 4.2, 1.0, theme.org_name.upper(), theme, 13, True, "#FFFFFF")
    _text(s, 0.6, 6.1, 4.2, 0.8, theme.tagline, theme, 12, False, "#FFFFFF", italic=True)
    _text(s, 6.0, 2.2, 6.6, 2.2, title, theme, 40, True, font=theme.heading_font, anchor=MSO_ANCHOR.BOTTOM, space=0)
    _text(s, 6.0, 4.55, 6.4, 1.4, subtitle, theme, 17, False, theme.muted)
    _text(s, 6.0, 6.6, 6.4, 0.4, date.today().strftime("%B %Y"), theme, 11, False, theme.muted)
    return s


def slide_statement(prs, theme: Theme, statement: str, support: str = "", notes: str = ""):
    s = _new_slide(prs, theme, notes)
    _rect(s, 0, 0, 13.333, 7.5, theme.tint)
    _rect(s, 0.9, 2.2, 0.12, 2.6, theme.accent)
    _text(s, 1.3, 2.1, 10.8, 1.9 if support else 2.8, statement, theme, 38, True, font=theme.heading_font,
          anchor=MSO_ANCHOR.BOTTOM if support else MSO_ANCHOR.MIDDLE)
    if support:
        _text(s, 1.3, 4.15, 10.4, 1.4, support, theme, 20, False, theme.muted)
    _logo(s, theme, 12.05, 0.45, 0.5)
    return s


def slide_story(prs, theme: Theme, headline: str, lines: list[str], kicker: str = "", notes: str = ""):
    s = _page(prs, theme, headline, kicker, notes)
    y = 2.35
    for i, line in enumerate(lines[:4]):
        _rect(s, 0.6, y + 0.12, 0.38, 0.38, theme.primary if i == 0 else _blend(theme.primary, "#FFFFFF", 0.22 * i),
              MSO_SHAPE.OVAL)
        _text(s, 0.6, y + 0.14, 0.38, 0.34, str(i + 1), theme, 12, True, "#FFFFFF", align=PP_ALIGN.CENTER)
        _text(s, 1.2, y + 0.06, 10.8, 0.95, line, theme, 19)
        y += 1.08
    return s


def slide_stats(prs, theme: Theme, headline: str, stats: list[dict], kicker: str = "", notes: str = ""):
    s = _page(prs, theme, headline, kicker, notes)
    stats = stats[:4] or [{"value": "–", "label": ""}]
    n = len(stats)
    w = (12.1 - 0.3 * (n - 1)) / n
    for i, st in enumerate(stats):
        x = 0.6 + i * (w + 0.3)
        _rect(s, x, 2.5, w, 3.3, theme.tint)
        _rect(s, x, 2.5, w, 0.09, theme.primary if i else theme.accent)
        _text(s, x + 0.35, 2.95, w - 0.7, 1.5, st["value"], theme, 54 if n < 4 else 44, True,
              theme.primary, theme.heading_font)
        _text(s, x + 0.35, 4.45, w - 0.7, 1.2, st["label"], theme, 16, False, theme.ink)
    return s


def slide_chart(prs, theme: Theme, headline: str, chart: dict, takeaway: str = "", kicker: str = "", notes: str = ""):
    s = _page(prs, theme, headline, kicker, notes)
    kind = chart_kind(chart)
    if kind == "before_after":
        add_chart(s, chart, 0.6, 2.2, 6.0, 4.5, theme)
    else:
        add_chart(s, chart, 0.6, 2.15, 8.3, 4.65, theme)
    x = 7.1 if kind == "before_after" else 9.3
    if takeaway:
        _rect(s, x, 2.35, 0.08, 2.4, theme.accent)
        _text(s, x + 0.3, 2.3, 12.7 - x - 0.3, 2.6, takeaway, theme, 18, False)
    _text(s, x + 0.3, 5.2 if takeaway else 2.3, 12.7 - x - 0.3, 1.5, chart.get("note", ""), theme, 10.5, False, theme.muted)
    return s


def slide_two_charts(prs, theme: Theme, headline: str, charts: list[dict], kicker: str = ""):
    s = _page(prs, theme, headline, kicker)
    for i, ch in enumerate(charts[:2]):
        x = 0.6 + i * 6.25
        _text(s, x, 2.1, 5.9, 0.6, short(ch.get("short_title") or ch["title"], 100), theme, 13, True,
              font=theme.heading_font)
        add_chart(s, ch, x, 2.65, 5.9, 3.7, theme)
        _text(s, x, 6.35, 5.9, 0.6, short(ch.get("note", ""), 150), theme, 9.5, False, theme.muted)
    return s


def slide_logic(prs, theme: Theme, headline: str, logic_model: dict, body: list[str] | None = None,
                kicker: str = "", notes: str = ""):
    s = _page(prs, theme, headline, kicker, notes)
    # The organization's own theory of change, not a paraphrase; the agent's line is a fallback.
    toc = logic_model.get("theory_of_change", "") or (body[0] if body else "")
    _text(s, 0.6, 2.05, 12.1, 1.3, short(toc, 330), theme, 15, False, theme.ink, italic=True)
    cols = [("What we do", logic_model.get("activities", [])),
            ("What changes first", logic_model.get("short_term_outcomes", [])),
            ("What lasts", logic_model.get("long_term_outcomes", []))]
    for i, (title, items) in enumerate(cols):
        x = 0.6 + i * 4.1
        color = [theme.quiet, _blend(theme.primary, "#FFFFFF", 0.4), theme.primary][i]
        _rect(s, x, 3.55, 3.8, 0.55, color, MSO_SHAPE.PENTAGON if i < 2 else MSO_SHAPE.RECTANGLE)
        _text(s, x + 0.2, 3.6, 3.4, 0.45, title.upper(), theme, 12, True, "#FFFFFF" if i else theme.ink)
        _text(s, x + 0.1, 4.25, 3.6, 2.7, [f"• {short(it, 105)}" for it in items[:3]], theme, 12, space=6)
    return s


def slide_quote(prs, theme: Theme, quote: str, attribution: str = "A program participant", notes: str = ""):
    s = _new_slide(prs, theme, notes)
    _rect(s, 0, 0, 13.333, 7.5, theme.primary)
    _text(s, 0.9, 0.7, 2, 1.8, "“", theme, 140, True, theme.accent, "Georgia")
    _text(s, 1.6, 2.2, 10.2, 3.2, quote, theme, 32, False, "#FFFFFF", theme.heading_font, anchor=MSO_ANCHOR.MIDDLE)
    _text(s, 1.6, 5.6, 10, 0.5, f"— {attribution}", theme, 15, False, "#FFFFFF")
    return s


def slide_closing(prs, theme: Theme, headline: str, lines: list[str], notes: str = ""):
    s = _new_slide(prs, theme, notes)
    _rect(s, 0, 0, 13.333, 7.5, theme.primary)
    _rect(s, 0, 6.9, 13.333, 0.6, theme.accent)
    if theme.logo:
        _rect(s, 5.97, 0.8, 1.4, 1.4, "#FFFFFF", MSO_SHAPE.OVAL)
        _logo(s, theme, 6.14, 0.97, 1.06)
    _text(s, 1.2, 2.5, 10.9, 1.5, headline, theme, 40, True, "#FFFFFF", theme.heading_font, PP_ALIGN.CENTER)
    _text(s, 1.2, 4.1, 10.9, 2.2, lines[:4], theme, 17, False, "#FFFFFF", align=PP_ALIGN.CENTER)
    return s


# ============================================================ quick impact report (Dashboard download)


def _paired(prs, theme: Theme, head: str, charts: list[dict], kicker: str) -> None:
    """Two charts per slide; an odd one out gets a full-width slide instead of half an empty one."""
    for i in range(0, len(charts), 2):
        pair = charts[i:i + 2]
        if len(pair) == 2:
            slide_two_charts(prs, theme, head, pair, kicker)
        else:
            c = pair[0]
            slide_chart(prs, theme, c.get("short_title") or c["title"], c, kicker=kicker)


def quick_report_pptx(data: dict, org_name: str, logic_model: dict | None, theme: Theme | None = None) -> bytes:
    theme = theme or Theme(org_name=org_name)
    theme.org_name = org_name
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    lm = logic_model or {}
    charts = data["charts"]
    h = data["headline"]

    slide_cover(prs, theme, "Impact report", lm.get("program_name") or "Our results to date")
    stats = [{"value": str(h["participants"]), "label": "participants enrolled"},
             {"value": str(h["matched"]), "label": "answered both the starting and ending survey"}]
    if h.get("top_improvement"):
        stats.append({"value": f"{h['top_improvement']['pct']}%", "label": f"improved: {h['top_improvement']['metric'].lower()}"})
    slide_stats(prs, theme, "At a glance", stats, "Headline numbers")
    if lm:
        slide_logic(prs, theme, "How change happens", lm, kicker="Our theory of change")

    improved = next((c for c in charts if c["id"] == "improved"), None)
    if improved:
        slide_chart(prs, theme, "Most participants improved on what we measure", improved,
                    "The share of participants whose answers improved between the start and end of the program.",
                    "Outcomes")
    befores = [c for c in charts if c["id"].startswith("metric-")]
    befores = [{**c, "short_title": c.get("metric", c["title"])} for c in charts if c["id"].startswith("metric-")]
    _paired(prs, theme, "Before and after", befores, "Outcomes")
    _paired(prs, theme, "Who we serve", [c for c in charts if c["id"].startswith("demo-")], "Participants")
    _paired(prs, theme, "Program activity", [c for c in charts if c["id"].startswith("indicator-")][:6], "From our records")
    quotes = [q["text"] for q in data.get("open_responses", []) if 20 <= len(q["text"]) <= 220][:3]
    if quotes:
        s = _page(prs, theme, "In their words", "Participant reflections")
        for i, q in enumerate(quotes):
            x = 0.6 + i * 4.1
            _rect(s, x, 2.3, 3.8, 3.9, theme.tint)
            _text(s, x + 0.25, 2.35, 1, 1, "“", theme, 60, True, theme.accent, "Georgia")
            _text(s, x + 0.3, 3.2, 3.2, 2.9, q, theme, 15, False, italic=True)
        _text(s, 0.6, 6.4, 12, 0.4, "Shared anonymously. Check that no one can be identified before sharing.", theme, 10, False, theme.muted)
    slide_story(prs, theme, "About this data", [
        "Participants are known only by a code. Names are never collected.",
        "Change is measured with the same questions at the start and end, for people who answered both.",
        "Groups with fewer than 5 people are combined so no one can be identified.",
        "Program numbers come from the organization's own records.",
    ], "Method")
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()


# ============================================================ funder deck (Report Designer)


def funder_deck_pptx(draft: dict, data: dict, logic_model: dict | None, theme: Theme) -> bytes:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    charts = reports.chart_index(data)
    for sl in draft["slides"]:
        layout, head, body, notes = sl["layout"], sl["headline"], sl.get("body", []), sl.get("speaker_notes", "")
        if layout == "title":
            slide_cover(prs, theme, draft["deck_title"], draft["deck_subtitle"], notes)
        elif layout == "statement":
            slide_statement(prs, theme, head, body[0] if body else "", notes)
        elif layout == "stats" and sl.get("stats"):
            slide_stats(prs, theme, head, sl["stats"], notes=notes)
        elif layout == "chart" and sl.get("chart_id") in charts:
            ch = charts[sl["chart_id"]]
            slide_chart(prs, theme, head, ch, body[0] if body else "", notes=notes)
        elif layout == "logic":
            slide_logic(prs, theme, head, logic_model or {}, body, notes=notes)
        elif layout == "quote" and sl.get("quote"):
            slide_quote(prs, theme, sl["quote"], notes=notes)
        elif layout == "closing":
            seen = " ".join(body).lower()
            extra = [x for x in (theme.tagline, theme.contact) if x and x.lower() not in seen]
            slide_closing(prs, theme, head, list(dict.fromkeys(body)) + extra, notes)
        else:  # story, ask, or anything missing its data
            slide_story(prs, theme, head, body or [""], "Our ask" if layout == "ask" else "", notes)
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()


# ============================================================ one-page flyer (PDF)

_FONT_FILES = {  # Windows font files, registered if present
    "Georgia": ("georgia.ttf", "georgiab.ttf"), "Calibri": ("calibri.ttf", "calibrib.ttf"),
    "Arial": ("arial.ttf", "arialbd.ttf"), "Segoe UI": ("segoeui.ttf", "segoeuib.ttf"),
    "Century Gothic": ("GOTHIC.TTF", "GOTHICB.TTF"), "Garamond": ("GARA.TTF", "GARABD.TTF"),
    "Trebuchet MS": ("trebuc.ttf", "trebucbd.ttf"), "Verdana": ("verdana.ttf", "verdanab.ttf"),
}


@cache
def _linux_fonts() -> dict[str, Path]:
    """Installed font files by name (wherever the distro put them)."""
    root = Path("/usr/share/fonts")
    return {p.name: p for p in root.rglob("*.ttf")} if root.is_dir() else {}


def _pdf_fonts(name: str) -> tuple[str, str]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    candidates = [(windows / f for f in _FONT_FILES.get(name, ()))]
    serif = name in ("Georgia", "Garamond")
    # On a Linux server (the Dockerfile installs these): open fonts with the same metrics as the Office ones.
    open_files = (("Carlito-Regular.ttf", "Carlito-Bold.ttf") if name == "Calibri" else
                  ("LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf") if serif else
                  ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"))
    linux = _linux_fonts()
    for pair in (open_files, ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")):
        candidates.append(linux.get(f, Path("/missing")) for f in pair)
    for paths in candidates:
        paths = list(paths)
        if len(paths) == 2 and all(p.exists() for p in paths):
            reg, bold = f"{name}-R", f"{name}-B"
            if reg not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(reg, str(paths[0])))
                pdfmetrics.registerFont(TTFont(bold, str(paths[1])))
            return reg, bold
    return ("Times-Roman", "Times-Bold") if serif else ("Helvetica", "Helvetica-Bold")


def _pdf_chart(chart: dict, theme: Theme, w: float, h: float, body_font: str):
    """A small horizontal-bar (or line) chart for the flyer, drawn with reportlab graphics."""
    from reportlab.graphics.charts.barcharts import HorizontalBarChart
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib import colors

    d = Drawing(w, h)
    unit = chart.get("unit", "")
    kind = chart_kind(chart)
    if kind == "line":
        lc = HorizontalLineChart()
        lc.x, lc.y, lc.width, lc.height = 34, 18, w - 44, h - 30
        lc.data = [[v or 0 for v in chart["series"][0]["values"]]]
        lc.categoryAxis.categoryNames = [short_month(c) for c in chart["categories"]]
        lc.categoryAxis.labels.fontName, lc.categoryAxis.labels.fontSize = body_font, 7
        lc.valueAxis.labels.fontName, lc.valueAxis.labels.fontSize = body_font, 7
        lc.valueAxis.valueMin = 0
        lc.valueAxis.strokeColor = colors.HexColor(theme.quiet)
        lc.categoryAxis.strokeColor = colors.HexColor(theme.quiet)
        lc.lines[0].strokeColor = colors.HexColor(theme.primary)
        lc.lines[0].strokeWidth = 2
        d.add(lc)
        return d
    cats = ["Before", "After"] if kind == "before_after" else [wrap2(c, 24) for c in chart["categories"]][:6]
    values = [(v or 0) for v in chart["series"][-1]["values"]][: len(cats)]
    bc = HorizontalBarChart()
    bc.x, bc.y, bc.width, bc.height = 112, 4, w - 148, h - 8
    bc.data = [list(reversed(values))]
    bc.categoryAxis.categoryNames = list(reversed(cats))
    bc.categoryAxis.labels.fontName, bc.categoryAxis.labels.fontSize = body_font, 8
    bc.categoryAxis.labels.boxAnchor = "e"
    bc.categoryAxis.strokeColor = colors.HexColor(theme.quiet)
    bc.valueAxis.visible = False
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100 if unit == "%" else max(values + [1]) * 1.15
    bc.bars.strokeColor = None
    bc.barWidth = 9
    bc.groupSpacing = 6
    for i in range(len(values)):
        is_before = kind == "before_after" and i == len(values) - 1  # reversed: "Before" is drawn last
        bc.bars[(0, i)].fillColor = colors.HexColor(theme.quiet if is_before else theme.primary)
    whole = all(float(v).is_integer() for v in values)
    bc.barLabelFormat = lambda v: fmt_value(round(v) if whole else v, unit)
    bc.barLabels.fontName, bc.barLabels.fontSize = body_font, 8
    bc.barLabels.boxAnchor, bc.barLabels.dx = "w", 3
    d.add(bc)
    return d


def one_pager_pdf(draft: dict, data: dict, theme: Theme) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader, simpleSplit
    from reportlab.pdfgen import canvas

    op = draft["one_pager"]
    reg, bold = _pdf_fonts(theme.body_font)
    hreg, hbold = _pdf_fonts(theme.heading_font)
    W, H = letter
    M = 40
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle(f"{theme.org_name}: impact one-pager")
    c.setAuthor(theme.org_name)

    def para(text, x, y, width, font, size, color, leading=None):
        leading = leading or size * 1.32
        c.setFont(font, size)
        c.setFillColor(colors.HexColor(color))
        for line in simpleSplit(text, font, size, width):
            c.drawString(x, y, line)
            y -= leading
        return y

    # header band
    band = 210
    c.setFillColor(colors.HexColor(theme.primary))
    c.rect(0, H - band, W, band, stroke=0, fill=1)
    c.setFillColor(colors.HexColor(theme.accent))
    c.rect(0, H - band - 6, W, 6, stroke=0, fill=1)
    x_text = M
    if theme.logo:
        c.setFillColor(colors.white)
        c.circle(M + 34, H - 62, 34, stroke=0, fill=1)
        c.drawImage(ImageReader(io.BytesIO(theme.logo)), M + 8, H - 88, 52, 52, mask="auto", preserveAspectRatio=True)
        x_text = M + 84
    c.setFillColor(colors.white)
    c.setFont(bold, 10)
    c.drawString(x_text, H - 52, theme.org_name.upper())
    if theme.tagline:
        c.setFont(reg, 9.5)
        c.drawString(x_text, H - 67, theme.tagline)
    y = para(op["headline"], M, H - 128, W - 2 * M, hbold, 26, "#FFFFFF", 30)
    para(op["subhead"], M, y - 2, W - 2 * M, reg, 11.5, "#FFFFFF")

    # stat tiles
    stats = op["stats"][:4]
    n = max(1, len(stats))
    gap = 10
    tw = (W - 2 * M - gap * (n - 1)) / n
    ty = H - band - 6 - 22 - 88
    for i, st in enumerate(stats):
        x = M + i * (tw + gap)
        c.setFillColor(colors.HexColor(theme.tint))
        c.rect(x, ty, tw, 88, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(theme.primary if i else theme.accent))
        c.rect(x, ty + 85, tw, 3, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(theme.primary))
        c.setFont(hbold, 26 if n < 4 else 22)
        c.drawString(x + 12, ty + 50, st["value"])
        para(st["label"], x + 12, ty + 34, tw - 24, reg, 9, theme.ink, 11)

    # story
    y = ty - 26
    c.setFont(bold, 9)
    c.setFillColor(colors.HexColor(theme.muted))
    c.drawString(M, y, "THE CHANGE WE SEE")
    y = para(op["story"], M, y - 16, W - 2 * M, reg, 11, theme.ink, 15)

    # charts
    charts = reports.chart_index(data)
    picked = [charts[i] for i in op.get("chart_ids", []) if i in charts][:2]
    if picked:
        y -= 10
        cw = (W - 2 * M - 16) / len(picked)
        for i, ch in enumerate(picked):
            x = M + i * (cw + 16)
            c.setFont(hbold, 10.5)
            c.setFillColor(colors.HexColor(theme.ink))
            title = ch.get("metric") or ch["title"]
            c.drawString(x, y, short(title, 58))
            drawing = _pdf_chart(ch, theme, cw, 118, reg)
            drawing.drawOn(c, x, y - 128)
        y -= 140

    # quote
    if op.get("quote"):
        lines = simpleSplit(f"“{op['quote']}”", hreg, 13, W - 2 * M - 40)
        qh = 18 * len(lines) + 30
        c.setFillColor(colors.HexColor(theme.tint))
        c.rect(M, y - qh, W - 2 * M, qh, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(theme.accent))
        c.rect(M, y - qh, 4, qh, stroke=0, fill=1)
        yy = y - 22
        for line in lines:
            c.setFont(hreg, 13)
            c.setFillColor(colors.HexColor(theme.ink))
            c.drawString(M + 20, yy, line)
            yy -= 18
        c.setFont(reg, 8.5)
        c.setFillColor(colors.HexColor(theme.muted))
        c.drawString(M + 20, y - qh + 9, "— A program participant")
        y -= qh + 14

    # call to action band
    c.setFillColor(colors.HexColor(theme.secondary))
    c.rect(0, 46, W, 62, stroke=0, fill=1)
    para(op["call_to_action"], M, 84, W - 2 * M, bold, 12.5, "#FFFFFF", 15)
    if theme.contact:
        c.setFont(reg, 9.5)
        c.setFillColor(colors.white)
        c.drawString(M, 56, theme.contact)
    c.setFont(reg, 7.5)
    c.setFillColor(colors.HexColor(theme.muted))
    c.drawString(M, 28, "Participant information is reported only in totals; groups under 5 people are not shown. "
                        "Built with Through Line.")
    c.showPage()
    c.save()
    return buf.getvalue()
