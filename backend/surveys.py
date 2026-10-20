"""Survey tools: built from the approved measurement plan, checked, answered, and scored.

A question (stored as JSON on Instrument.questions):
  {id, text, scale, metric, source: "plan"|"staff", hidden, waves: ["pre","post"], reverse, note}

The questions come straight from the metrics the client approved: every
switched-on question of every metric that a collection tool covers. Staff can
then hide questions, add open-response questions, choose which wave asks a
question, mark negatively worded items as reverse-scored, and add demographics.
Once responses exist, existing questions can't be reworded or re-scaled (that
would break pre/post comparison). They can only be hidden, and new questions added.
"""

import re
import secrets
from typing import Any

SCALES: dict[str, dict[str, Any]] = {
    "agree_5": {"label": "Agree (1–5)", "options": ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]},
    "confidence_5": {"label": "Confidence (1–5)",
                     "options": ["Not at all confident", "A little confident", "Somewhat confident", "Very confident",
                                 "Extremely confident"]},
    "frequency_5": {"label": "How often (1–5)", "options": ["Never", "Rarely", "Sometimes", "Often", "Always"]},
    "scale_0_10": {"label": "Rating 0–10", "options": [str(i) for i in range(11)]},
    "yes_no": {"label": "Yes / No", "options": ["No", "Yes"]},
    "number": {"label": "Number", "options": None},
    "open_text": {"label": "Written answer", "options": None},
}
SCORED = {"agree_5", "confidence_5", "frequency_5", "scale_0_10", "yes_no", "number"}
MAX_VALUE = {"agree_5": 5, "confidence_5": 5, "frequency_5": 5, "scale_0_10": 10, "yes_no": 1}
MIN_VALUE = {"agree_5": 1, "confidence_5": 1, "frequency_5": 1, "scale_0_10": 0, "yes_no": 0}

PREFER_NOT = "Prefer not to say"
DEMOGRAPHICS: dict[str, dict[str, Any]] = {
    "age_range": {"label": "What is your age?", "multi": False,
                  "options": ["Under 18", "18–24", "25–34", "35–44", "45–54", "55–64", "65 or older", PREFER_NOT]},
    "gender": {"label": "What is your gender?", "multi": False,
               "options": ["Woman", "Man", "Non-binary", "Another identity", PREFER_NOT]},
    "race_ethnicity": {"label": "How do you describe your race or ethnicity? (choose all that apply)", "multi": True,
                       "options": ["Asian", "Black or African American", "Hispanic or Latino/a/e",
                                   "Middle Eastern or North African", "Native American or Alaska Native",
                                   "Native Hawaiian or Pacific Islander", "White", "Another race or ethnicity",
                                   PREFER_NOT]},
    "primary_language": {"label": "What language do you speak most at home?", "multi": False,
                         "options": ["English", "Spanish", "Haitian Creole", "Arabic", "Dari or Pashto",
                                     "Another language", PREFER_NOT]},
    "town": {"label": "Which town do you live in?", "multi": False,
             "options": ["New Haven", "West Haven", "Hamden", "East Haven", "Another town", PREFER_NOT]},
    "household": {"label": "Do you have children under 18 living with you?", "multi": False,
                  "options": ["Yes", "No", PREFER_NOT]},
}
WAVES = ("pre", "post")


def new_qid() -> str:
    return "q_" + secrets.token_hex(4)


# ============================================================ building from the plan


def build_from_plan(plan: dict) -> tuple[list[dict], list[dict]]:
    """Return (instruments, indicators) from an approved measurement plan.

    participant_survey / staff_assessment tools -> instruments; program_records metrics -> indicators.
    """
    metrics = {m["name"]: m for m in plan.get("metrics", [])}
    instruments, used = [], set()
    for tool in plan.get("tools", []):
        if tool.get("method") not in ("participant_survey", "staff_assessment"):
            continue
        questions = []
        for name in tool.get("metrics", []):
            m = metrics.get(name)
            if not m or m.get("method") == "program_records":
                continue
            used.add(name)
            for q in m.get("questions", []):
                if not q.get("included", True) or not q.get("text", "").strip():
                    continue
                questions.append({
                    "id": new_qid(), "text": q["text"].strip(), "scale": q["scale"], "metric": name,
                    "source": "plan", "hidden": False, "reverse": False, "note": q.get("note") or "",
                    # Reflections are most useful after the program; everything else is asked pre and post.
                    "waves": ["post"] if q["scale"] == "open_text" else ["pre", "post"],
                })
        instruments.append({"name": tool["name"], "method": tool["method"], "when": tool.get("when", ""),
                            "questions": questions})
    # Survey metrics no tool mentioned still get asked: add them to the first matching instrument.
    for name, m in metrics.items():
        if name in used or m.get("method") == "program_records":
            continue
        target = next((i for i in instruments if i["method"] == m["method"]), None)
        if target is None:
            target = {"name": f"{m['name']} check-in", "method": m["method"], "when": m.get("timing", ""),
                      "questions": []}
            instruments.append(target)
        for q in m.get("questions", []):
            if q.get("included", True) and q.get("text", "").strip():
                target["questions"].append({
                    "id": new_qid(), "text": q["text"].strip(), "scale": q["scale"], "metric": name,
                    "source": "plan", "hidden": False, "reverse": False, "note": q.get("note") or "",
                    "waves": ["post"] if q["scale"] == "open_text" else ["pre", "post"]})
    indicators = []
    for m in metrics.values():
        if m.get("method") != "program_records":
            continue
        qs = [q for q in m.get("questions", []) if q.get("included", True)] or [{"text": m["name"]}]
        for q in qs:
            indicators.append({"name": q["text"].strip().rstrip("?"), "unit": "", "description": m.get("how_scored", ""),
                               "source": "plan"})
    return instruments, indicators


# ============================================================ editing rules


def validate_questions(questions: list[dict]) -> list[dict]:
    clean = []
    for q in questions:
        if q.get("scale") not in SCALES:
            raise ValueError(f"Unknown scale: {q.get('scale')}")
        waves = [w for w in q.get("waves", WAVES) if w in WAVES]
        if not waves:
            raise ValueError("Every question needs to be asked at pre, post, or both.")
        text = str(q.get("text", "")).strip()
        if not text:
            raise ValueError("Questions can't be blank.")
        clean.append({"id": q.get("id") or new_qid(), "text": text[:400], "scale": q["scale"],
                      "metric": q.get("metric"), "source": q.get("source", "staff"),
                      "hidden": bool(q.get("hidden")), "reverse": bool(q.get("reverse")),
                      "note": str(q.get("note") or "")[:300], "waves": waves})
    return clean


def locked_changes(old: list[dict], new: list[dict]) -> str | None:
    """With responses already in, existing questions may only be hidden/shown. Returns a problem, or None."""
    new_by_id = {q["id"]: q for q in new}
    for q in old:
        n = new_by_id.get(q["id"])
        if n is None:
            return "Questions that already have answers can't be deleted. Hide them instead."
        if n["text"] != q["text"] or n["scale"] != q["scale"] or n["reverse"] != q["reverse"]:
            return "Questions that already have answers can't be reworded or re-scaled (it would break pre/post comparison). Hide it and add a new one instead."
    return None


# ============================================================ automatic checks (no AI)


def precheck(questions: list[dict], method: str) -> list[dict]:
    """Deterministic checks the Survey Review Bot also sees. Same shape as the bot's issues."""
    issues = []
    visible = [q for q in questions if not q["hidden"]]
    by_metric: dict[str, set[str]] = {}
    for q in visible:
        if q.get("metric") and q["scale"] != "open_text":
            by_metric.setdefault(q["metric"], set()).add(q["scale"])
    for metric, scales in by_metric.items():
        if len(scales) > 1:
            issues.append({"question_id": None, "kind": "scale_consistency", "severity": "high",
                           "problem": f"'{metric}' mixes scales ({', '.join(SCALES[s]['label'] for s in sorted(scales))}), "
                                      "so its questions can't be averaged into one score.",
                           "suggestion": "Use one scale for every question in this metric.", "fix": None})
    for q in visible:
        if q["scale"] in SCORED and q["scale"] != "number" and q["waves"] == ["post"]:
            issues.append({"question_id": q["id"], "kind": "insight", "severity": "medium",
                           "problem": "This rated question is only asked after the program, so you can't see change.",
                           "suggestion": "Ask it at both pre and post.",
                           "fix": {"action": "set_waves", "waves": ["pre", "post"]}})
        if re.search(r"\b(and|or)\b", q["text"], re.I) and q["scale"] in {"agree_5", "confidence_5", "frequency_5"} \
                and len(q["text"]) > 60:
            issues.append({"question_id": q["id"], "kind": "wording", "severity": "low",
                           "problem": "This question may ask about two things at once.",
                           "suggestion": "Check that it asks about one idea only.", "fix": None})
    if method == "participant_survey":
        rated = [q for q in visible if q["scale"] != "open_text"]
        if len(visible) > 15:
            issues.append({"question_id": None, "kind": "burden", "severity": "medium",
                           "problem": f"{len(visible)} visible questions may be too long for participants.",
                           "suggestion": "Aim for about 10–12. Hide the least essential ones.", "fix": None})
        if not any(q["scale"] == "open_text" for q in visible):
            issues.append({"question_id": None, "kind": "insight", "severity": "low",
                           "problem": "There's no open-response question, so you won't hear participants in their own words.",
                           "suggestion": "Add one reflection question at post.",
                           "fix": {"action": "add_open_question",
                                   "text": "What has changed for you since you started the program?"}})
        if not rated:
            issues.append({"question_id": None, "kind": "insight", "severity": "high",
                           "problem": "No rated questions are visible, so nothing can be compared pre to post.",
                           "suggestion": "Show at least one rated question per metric.", "fix": None})
    return issues


# ============================================================ answering


def questions_for(questions: list[dict], wave: str) -> list[dict]:
    return [q for q in questions if not q["hidden"] and wave in q["waves"]]


def clean_answers(questions: list[dict], wave: str, answers: dict[str, Any], *, partial_ok: bool = True) -> dict:
    """Keep only valid answers to this wave's questions. Unanswered questions are simply left out."""
    out = {}
    for q in questions_for(questions, wave):
        v = answers.get(q["id"])
        if v is None or v == "":
            continue
        scale = q["scale"]
        if scale == "open_text":
            out[q["id"]] = str(v).strip()[:2000]
        elif scale == "number":
            try:
                num = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"'{q['text']}' needs a number.")
            if num < 0 or num > 1_000_000:
                raise ValueError(f"'{q['text']}' is out of range.")
            out[q["id"]] = num
        else:
            try:
                num = int(v)
            except (TypeError, ValueError):
                raise ValueError(f"'{q['text']}' needs one of the choices.")
            if not MIN_VALUE[scale] <= num <= MAX_VALUE[scale]:
                raise ValueError(f"'{q['text']}' is out of range.")
            out[q["id"]] = num
    return out


def clean_demographics(keys: list[str], values: dict[str, Any]) -> dict:
    out = {}
    for key in keys:
        spec = DEMOGRAPHICS.get(key)
        v = values.get(key)
        if not spec or v in (None, "", []):
            continue
        if spec["multi"]:
            chosen = [x for x in (v if isinstance(v, list) else [v]) if x in spec["options"]]
            if chosen:
                out[key] = chosen
        elif v in spec["options"]:
            out[key] = v
    return out


# ============================================================ scoring


def scored_value(q: dict, raw: Any) -> float | None:
    """Numeric value for analysis, with reverse-scored items flipped (so higher always means better)."""
    if raw is None or q["scale"] not in SCORED:
        return None
    v = float(raw)
    if q.get("reverse") and q["scale"] in MAX_VALUE:
        v = MAX_VALUE[q["scale"]] + MIN_VALUE[q["scale"]] - v
    return v


def metric_score(questions: list[dict], answers: dict) -> dict[str, float]:
    """Mean scored value per metric for one response (questions sharing a metric and scale)."""
    sums: dict[str, list[float]] = {}
    for q in questions:
        if q.get("metric") and q["scale"] in SCORED and q["id"] in answers:
            v = scored_value(q, answers[q["id"]])
            if v is not None:
                sums.setdefault(q["metric"], []).append(v)
    return {m: sum(v) / len(v) for m, v in sums.items() if v}


def metric_scale(questions: list[dict], metric: str) -> str | None:
    scales = {q["scale"] for q in questions if q.get("metric") == metric and q["scale"] in SCORED}
    return next(iter(scales)) if len(scales) == 1 else ("mixed" if scales else None)
