"""Live numbers for reports and grant drafts.

Agents never type numbers. They write {{key}} tokens from a catalog built here
(e.g. "{{improved:housing-stability}} of families who answered both surveys"),
and the app fills each token with the latest value every time a report or grant
draft is viewed or downloaded. That is what lets one AI-designed report "shell"
stay current as new surveys and program numbers come in, with no new AI call.

Keys are built from names (metric, category, number), not positions, so they
stay the same as data is added.
"""

import re
from typing import Any

from design import fmt_value, short_month
from reports import HIDDEN, slug

TOKEN = re.compile(r"\{\{\s*([a-z0-9:_\-]+)\s*\}\}")
MISSING = "–"


def catalog(data: dict) -> dict[str, dict[str, str]]:
    """{key: {"value": "85%", "label": "..."}} from reports.compute() output."""
    h = data["headline"]
    out: dict[str, dict[str, str]] = {
        "participants": {"value": f"{h['participants']:,}", "label": "participants enrolled"},
        "matched": {"value": f"{h['matched']:,}", "label": "participants who answered both the pre and post survey"},
        "pre_surveys": {"value": f"{h['responses_pre']:,}", "label": "pre surveys completed"},
        "post_surveys": {"value": f"{h['responses_post']:,}", "label": "post surveys completed"},
    }
    if h.get("top_improvement"):
        out["top_improvement"] = {"value": f"{h['top_improvement']['pct']}%",
                                  "label": f"improved on {h['top_improvement']['metric']}"}
    for c in data["charts"]:
        cid, unit = c["id"], c.get("unit", "")
        if cid == "improved":
            for cat, v in zip(c["categories"], c["series"][0]["values"]):
                out[f"improved:{slug(cat)}"] = {"value": fmt_value(v, "%"),
                                                "label": f"of matched participants improved on {cat}"}
        elif cid.startswith("metric-"):
            name = c.get("metric", c["title"])
            before, after = c["series"][0]["values"][:2]
            pct = unit.startswith("%")
            out[f"before:{slug(name)}"] = {"value": fmt_value(before, "%" if pct else ""),
                                           "label": f"{name} before (pre), {'share answering yes' if pct else 'average'}"}
            out[f"after:{slug(name)}"] = {"value": fmt_value(after, "%" if pct else ""),
                                          "label": f"{name} after (post), {'share answering yes' if pct else 'average'}"}
        elif cid.startswith("demo-"):
            for cat, v in zip(c["categories"], c["series"][0]["values"]):
                if cat != HIDDEN:
                    out[f"share:{cid[5:]}:{slug(cat)}"] = {"value": fmt_value(v, "%"),
                                                          "label": f"of participants: {c['title'].lower()} = {cat}"}
        elif cid.startswith("choice-"):  # the latest wave asked: share who picked each choice
            latest = c["series"][-1]
            for cat, v in zip(c["categories"], latest["values"]):
                out[f"answer:{slug(c['title'])[:40]}:{slug(cat)}"] = {
                    "value": fmt_value(v, "%"), "label": f"of people answering '{c['title']}' ({latest['name']}) chose {cat}"}
        elif cid.startswith("indicator-"):
            values = c["series"][0]["values"]
            months = c["categories"]
            key = slug(c["title"])
            out[f"latest:{key}"] = {"value": fmt_value(values[-1], unit),
                                    "label": f"{c['title']}, latest month ({short_month(months[-1])})"}
            if unit == "$" or len(months) > 1:
                out[f"total:{key}"] = {"value": fmt_value(sum(v or 0 for v in values), unit),
                                       "label": f"{c['title']}, total over {len(months)} months "
                                                f"({short_month(months[0])}–{short_month(months[-1])})"}
    return out


def for_agent(cat: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    """The list the agent sees: key, current value (so it can judge the story), and meaning."""
    return [{"key": k, "current_value": v["value"], "meaning": v["label"]} for k, v in cat.items()]


def unknown_keys(obj: Any, cat: dict) -> set[str]:
    found: set[str] = set()

    def walk(o):
        if isinstance(o, str):
            found.update(k for k in TOKEN.findall(o) if k not in cat)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return found


def fill(obj: Any, cat: dict) -> Any:
    """Replace every {{key}} with its latest value ("–" if that number no longer exists)."""
    if isinstance(obj, str):
        return TOKEN.sub(lambda m: cat.get(m.group(1), {}).get("value", MISSING), obj)
    if isinstance(obj, dict):
        return {k: fill(v, cat) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fill(v, cat) for v in obj]
    return obj
