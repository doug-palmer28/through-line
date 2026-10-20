"""Demo backend: the real app with scripted agents instead of gpt-6-luna.

For clicking through the UI without spending tokens. No API key is used, and
the audit log and session records go to a temp folder, not output/ or data/.

    .venv/Scripts/python tests/demo_server.py      (serves on port 8000)
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

os.environ["PORTKEY_API_KEY"] = ""  # empty, not missing: stops load_dotenv from restoring the real key
_tmp = Path(tempfile.mkdtemp(prefix="throughline_demo_"))
os.environ["THROUGH_LINE_AUDIT"] = str(_tmp / "audit_log.json")
os.environ["THROUGH_LINE_SESSIONS"] = str(_tmp / "sessions")
os.environ["THROUGH_LINE_DB"] = str(_tmp / "demo.db")
os.environ["THROUGH_LINE_SECRET"] = "demo-only-secret-" + os.urandom(16).hex()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import uvicorn  # noqa: E402
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart  # noqa: E402
from pydantic_ai.models.function import AgentInfo, FunctionModel  # noqa: E402

from agents import common  # noqa: E402

LOGIC_MODEL = {
    "program_name": "Pathways Home case management",
    "theory_of_change": "If we pair families experiencing homelessness with a dedicated case manager and help them "
                        "secure and keep housing, then they will stabilize and stay housed, because housing comes "
                        "first and steady support helps families handle setbacks before they become crises.",
    "inputs": ["3 case managers", "Landlord partner network", "City and foundation grants", "Volunteer move-in team"],
    "activities": ["Weekly case management meetings", "Housing search and landlord matching",
                   "Move-in support and furnishing", "Referrals to benefits and childcare"],
    "outputs": ["Families enrolled", "Case management sessions held", "Families placed in housing",
                "Benefit applications submitted"],
    "short_term_outcomes": ["Families move into stable housing", "Families access benefits they qualify for",
                            "Parents feel more confident managing a household budget"],
    "long_term_outcomes": ["Families remain housed after 12 months", "Children stay enrolled in one school",
                           "Fewer returns to shelter"],
    "assumptions": ["Affordable units remain available through landlord partners",
                    "Families choose to engage with weekly meetings"],
    "external_factors": ["Local rent increases", "Changes to public benefit rules"],
}

FIELD_SOURCES = [
    {"id": "S1", "title": "Continuum of Care (CoC) Program", "publisher": "HUD Exchange",
     "url": "https://www.hudexchange.info/programs/coc/", "note": "CoC grantees report exits to permanent housing and returns to homelessness."},
    {"id": "S2", "title": "Rapid Re-Housing resources", "publisher": "National Alliance to End Homelessness",
     "url": "https://endhomelessness.org/", "note": "Frames rapid rehousing success as fast placement and lasting stability."},
    {"id": "S3", "title": "Financial Well-Being Scale", "publisher": "Consumer Financial Protection Bureau",
     "url": "https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/",
     "note": "A free, validated set of items on financial security and freedom of choice."},
]

CANNED = {
    "IntakeResult": {
        "snapshot": {"org_name": "Demo org", "sector": "homelessness services: rapid rehousing for families",
                     "mission": "Help families move from shelter into stable homes.",
                     "populations_served": ["Families with children in emergency shelter"],
                     "programs": ["Pathways Home"], "activities": ["Case management", "Housing search"],
                     "resources": ["3 case managers"], "outcomes_claimed": ["Families housed"],
                     "existing_measures": ["Number of families placed"],
                     "gaps": ["How long families stay housed", "What changes families notice"]},
        "welcome_message": "Thanks for sharing your materials. We read about Pathways Home and your focus on "
                           "moving families from shelter into stable homes. We have five questions to fill in the picture.",
        "upload_request": "If you have it, your most recent annual report would help us see your numbers.",
    },
    "FirstQuestion": {"question": "Who exactly does Pathways Home serve, and what situation are families usually in "
                                  "when they come to you?",
                      "why_we_ask": "Knowing who you serve anchors every part of the logic model."},
    "SectorBrief": {"sector": "homelessness services", "common_outcomes": ["Housing placement", "Housing retention"],
                    "best_practices": ["Housing First", "Progressive engagement"],
                    "standards_and_frameworks": ["HUD System Performance Measures", "Self-Sufficiency Matrix"],
                    "common_metrics": ["Retention at 12 months"], "pitfalls": ["Counting placements only"],
                    "caveat": "Based on general field knowledge.",
                    "suggested_questions": [{"question": "How long do families usually stay in your program?",
                                             "why": "Dosage shapes realistic outcomes."}]},
    "FieldResearch": {
        "funder_priorities": [
            {"funder": "HUD Continuum of Care", "funder_type": "government",
             "what_they_want": "Exits to permanent housing and fewer returns to homelessness.", "source_ids": ["S1"]},
            {"funder": "Community foundations", "funder_type": "philanthropic",
             "what_they_want": "Housing stability plus family well-being stories.", "source_ids": ["S2"]},
        ],
        "compelling_metrics": ["Housing retention at 12 months [S1]", "Returns to homelessness [S1]"],
        "peer_models": [{"organization": "National Alliance to End Homelessness",
                         "how_they_frame_it": "Fast placement, then lasting stability.", "source_ids": ["S2"]}],
        "framing_tips": ["Lead with retention, not just placements."],
        "suggested_questions": [{"question": "Do you report to any government contract today?",
                                 "why": "Shows which measures you already owe funders."}],
        "sources": FIELD_SOURCES,
    },
    "MetricsResearch": {
        "suggestions": [
            {"outcome": "Families remain housed after 12 months", "measure": "Housing retention",
             "sample_questions": ["Is the family in the same home as at move-in?"], "who_uses_it": "HUD CoC",
             "source_ids": ["S1"]},
            {"outcome": "Parents feel more confident managing a household budget", "measure": "Financial well-being",
             "sample_questions": ["I could handle a major unexpected expense."], "who_uses_it": "CFPB scale users",
             "source_ids": ["S3"]},
        ],
        "sources": [
            {"id": "S1", "title": "Continuum of Care (CoC) Program", "publisher": "HUD Exchange",
             "url": "https://www.hudexchange.info/programs/coc/", "note": "Retention and returns."},
            {"id": "S2", "title": "Financial Well-Being Scale", "publisher": "Consumer Financial Protection Bureau",
             "url": "https://www.consumerfinance.gov/data-research/research-reports/financial-well-being-scale/",
             "note": "Free, validated items."},
        ],
    },
    "InterviewTurn": {"acknowledgement": "That's really helpful. It sounds like steady, weekly contact is the heart of your work.",
                      "learned": ["Weekly meetings are the core activity"],
                      "next_question": "What changes do you see in families after six months with you?",
                      "why_we_ask": "This tells us your short-term outcomes.", "upload_request": None},
    "DocumentNotes": {"notes": ["Served 64 families last year", "82% still housed at 6 months"],
                      "acknowledgement": "Thanks for the annual report. The housing retention numbers are really useful."},
    "MetricsResult": {
        "plan": {
            "summary": "Three metrics track whether families get housed, stay housed, and feel more in control, "
                       "using measures HUD and other funders already recognize.",
            "metrics": [
                {"name": "Housing stability", "outcome": "Families remain housed after 12 months",
                 "method": "staff_assessment",
                 "questions": [
                     {"text": "Is the family living in the same home as at move-in?", "scale": "yes_no", "included": True,
                      "note": "Mirrors HUD's housing retention measure", "source_ids": ["S1"]},
                     {"text": "Has the family returned to shelter since move-in?", "scale": "yes_no", "included": True,
                      "note": "HUD tracks returns to homelessness", "source_ids": ["S1"]},
                     {"text": "How many months has the family been in their current home?", "scale": "number",
                      "included": False, "source_ids": []},
                 ],
                 "timing": "At move-in, then 6 and 12 months later", "how_scored": "% of families still housed",
                 "why_it_matters": "Staying housed is the result funders care about most.",
                 "funder_relevance": "HUD Continuum of Care grantees report retention and returns [S1].",
                 "source_ids": ["S1"]},
                {"name": "Financial confidence", "outcome": "Parents feel more confident managing a household budget",
                 "method": "participant_survey",
                 "questions": [
                     {"text": "How confident are you that you can pay rent on time each month?", "scale": "confidence_5",
                      "included": True, "source_ids": []},
                     {"text": "I could handle a major unexpected expense.", "scale": "agree_5", "included": True,
                      "note": "Adapted from the CFPB Financial Well-Being Scale", "source_ids": ["S5"]},
                     {"text": "I am behind on my bills.", "scale": "frequency_5", "included": False,
                      "note": "Adapted from the CFPB Financial Well-Being Scale", "source_ids": ["S5"]},
                 ],
                 "timing": "Pre (enrollment) and post (week 12)", "how_scored": "% of parents who improve by 1+ point",
                 "why_it_matters": "Confidence with money predicts keeping a home.",
                 "funder_relevance": "Financial well-being items are free and widely recognized [S5].",
                 "source_ids": ["S5"]},
                {"name": "In their words", "outcome": "Families move into stable housing", "method": "participant_survey",
                 "questions": [{"text": "What has changed for your family since moving in?", "scale": "open_text",
                                "included": True, "source_ids": []},
                               {"text": "What helped most?", "scale": "open_text", "included": False, "source_ids": []}],
                 "timing": "Post (week 12)", "how_scored": "Themes and stories, shared only with permission",
                 "why_it_matters": "Stories show what the numbers mean.",
                 "funder_relevance": "Community foundations ask for family stories alongside numbers [S2].",
                 "source_ids": ["S2"]},
            ],
            "tools": [
                {"name": "Family check-in survey", "method": "participant_survey", "when": "Paper or phone, at enrollment and week 12",
                 "metrics": ["Financial confidence", "In their words"]},
                {"name": "Case manager housing check", "method": "staff_assessment", "when": "At move-in, 6 and 12 months",
                 "metrics": ["Housing stability"]},
            ],
        },
        "message_to_client": "Here's a measurement plan with three metrics, built on measures funders already use. "
                             "Switch questions on or off, edit anything, or tell us what to change.",
        "team_notes": ["Evaluation Specialist: same questions pre and post.",
                       "Client Advocate: kept the survey to 4 recommended questions.",
                       "Funder Researcher: aligned retention with HUD's measure."],
    },
    "DraftResult": {"logic_model": LOGIC_MODEL,
                    "alignment": [
                        {"note": "Long-term outcomes use HUD's framing: staying housed and not returning to shelter.",
                         "source_ids": ["S1"]},
                        {"note": "Short-term outcomes pair placement with stability, as rapid rehousing leaders do.",
                         "source_ids": ["S2"]}],
                    "message_to_client": "Here's a first draft of your logic model. Edit any line directly, or tell us "
                                         "what to change and we'll revise it.",
                    "team_notes": ["Sector Expert: retention at 12 months is the outcome funders expect.",
                                   "Client Advocate: kept your program name, Pathways Home.",
                                   "Evaluation Specialist: moved 'families placed' to outputs.",
                                   "Funder Researcher: worded long-term outcomes the way HUD reports them."]},
}

TITLES = {"evaluation_specialist": "# Evaluation Specialist", "client_advocate": "# Client Advocate",
          "sector_expert": "# Sector Expert", "funder_researcher": "# Funder Researcher"}
VOICES = {
    "sector_expert": ("Programs like this are judged on housing retention at 12 months.",
                      "Track retention, not just placements."),
    "client_advocate": ("This sounds like them, but keep the survey short; families are juggling a lot.",
                        "Use their name for the program, Pathways Home."),
    "evaluation_specialist": ("The chain holds: each outcome traces to weekly case management.",
                              "Ask the same questions pre and post."),
    "funder_researcher": ("HUD and local foundations will look for retention and returns to shelter.",
                          "Use HUD's wording for long-term outcomes."),
}


def _who(messages: list[ModelMessage]) -> str:
    text = str(messages[0]) if messages else ""
    return next((k for k, t in TITLES.items() if t in text), "sector_expert")


def _specialist(title: str, who: str) -> dict:
    summary, rec = VOICES[who]
    if title == "SpecialistQuestions":
        return {"specialist": who, "questions": [{"question": f"({who.replace('_', ' ')}) {rec}", "why": summary}]}
    if title == "SpecialistReview":
        return {"specialist": who, "verdict": "needs_changes", "keep": [summary], "change": [rec]}
    return {"specialist": who, "summary": summary, "recommendations": [rec], "concerns": [], "suggested_question": None}


def _survey_review(messages: list[ModelMessage]) -> dict:
    """Scripted Survey Review Bot: reads the real question ids from the survey it was given."""
    qs = _prompt_json(messages).get("questions", [])
    issues = []
    if qs:
        q = qs[0]
        issues.append({"question_id": q["id"], "kind": "wording", "severity": "medium",
                       "problem": "This question is a little long for a quick phone survey.",
                       "suggestion": "Shorten it while keeping the meaning.",
                       "fix": {"action": "rewrite", "text": q["text"].split(",")[0].rstrip("?") + "?"}})
    mixed = [q for q in qs if q.get("scale") == "confidence_5"]
    if mixed:
        issues.append({"question_id": mixed[0]["id"], "kind": "scale_consistency", "severity": "high",
                       "problem": "This metric mixes a confidence scale with an agreement scale.",
                       "suggestion": "Use the agreement scale for every question in this metric.",
                       "fix": {"action": "change_scale", "scale": "agree_5"}})
    if not any(q.get("scale") == "open_text" for q in qs):
        issues.append({"question_id": None, "kind": "insight", "severity": "low",
                       "problem": "No open question for participants' own words.", "suggestion": "Add one at post.",
                       "fix": {"action": "add_open_question", "text": "What has changed for you since you joined?"}})
    return {"summary": "Clear and short overall. Fix the mixed scale so the metric can be scored.",
            "ready": False, "strengths": ["Plain language", "Short enough for a phone"], "issues": issues}


def _prompt_json(messages: list[ModelMessage]) -> dict:
    """The JSON payload the route put in the user prompt (empty if there isn't one)."""
    import json as _json
    import re as _re

    from pydantic_ai.messages import UserPromptPart

    text = next((str(p.content) for msg in messages for p in getattr(msg, "parts", [])
                 if isinstance(p, UserPromptPart)), "")
    decoder = _json.JSONDecoder()
    found = {}
    for m in _re.finditer(r"(?:^|\n)\{", text):  # the last JSON block wins (revisions send the draft first)
        try:
            found = decoder.raw_decode(text[m.end() - 1:])[0]
        except ValueError:
            continue
    return found


def _report_draft(messages: list[ModelMessage]) -> dict:
    """Scripted Report Designer: a short deck built from the real chart ids, numbers, and quotes it was given."""
    data = _prompt_json(messages)
    org, charts, quotes = data.get("organization", "Our organization"), data.get("charts", []), data.get("quotes", [])
    keys = {n["key"] for n in data.get("numbers", [])}
    stats = [{"value": "{{participants}}", "label": "families enrolled"},
             {"value": "{{matched}}", "label": "completed pre and post surveys"}]
    if "top_improvement" in keys:
        stats.append({"value": "{{top_improvement}}", "label": "improved on our top outcome"})
    brand = data.get("design_standards", {})
    slides = [{"layout": "title", "headline": f"{org}: our impact so far", "body": [], "stats": [], "chart_id": None,
               "quote": None, "speaker_notes": "Thank the audience and set up the story."},
              {"layout": "statement", "headline": "Every family deserves a stable place to call home.", "body": [],
               "stats": [], "chart_id": None, "quote": None, "speaker_notes": "Open with why the work matters."},
              {"layout": "logic", "headline": "How change happens", "body": [], "stats": [], "chart_id": None,
               "quote": None, "speaker_notes": "Walk through the pathway from activities to outcomes."},
              {"layout": "stats", "headline": "This year in numbers", "body": [], "stats": stats, "chart_id": None,
               "quote": None, "speaker_notes": "Pause on each number."}]
    for c in charts[:4]:
        slides.append({"layout": "chart", "headline": c["title"], "body": ["The trend points the right way."],
                       "stats": [], "chart_id": c["id"], "quote": None, "speaker_notes": "Explain what the chart shows."})
    if quotes:
        slides.append({"layout": "quote", "headline": "In their words", "body": [], "stats": [], "chart_id": None,
                       "quote": quotes[0], "speaker_notes": "Let the quote land."})
    slides += [{"layout": "ask", "headline": "What your support makes possible", "body": ["Serve 20 more families",
                "Extend follow-up to 12 months"], "stats": [], "chart_id": None, "quote": None,
                "speaker_notes": "Make the ask concrete."},
               {"layout": "closing", "headline": "Thank you", "body": [], "stats": [], "chart_id": None, "quote": None,
                "speaker_notes": "Invite questions."}]
    return {"deck_title": f"{org}: impact to date", "deck_subtitle": data.get("audience", "Funders"), "slides": slides,
            "one_pager": {"headline": "Stable homes, stronger families", "subhead": f"{org} helps families stay housed.",
                          "stats": stats, "story": "Families who joined the program report more stability after six months.",
                          "chart_ids": [c["id"] for c in charts[:2]], "quote": quotes[0] if quotes else None,
                          "call_to_action": "Help us reach 20 more families next year."},
            "design": {"primary": brand.get("primary") or "#1F4E5F", "secondary": brand.get("secondary") or "#D98E04",
                       "accent": brand.get("accent") or "#F2C14E", "background": "#FFFFFF",
                       "heading_font": brand.get("heading_font") or "Georgia",
                       "body_font": brand.get("body_font") or "Calibri", "mood": "warm and plain"}}


def _foundation(messages: list[ModelMessage]) -> dict:
    """Scripted Funder Researcher, foundation job: a plausible profile with unverified sources."""
    name = _prompt_json(messages).get("foundation", "The Foundation")
    return {"foundation": name, "mission": f"{name} invests in families and neighborhoods across the region.",
            "priorities": [{"priority": "Housing stability for families with children", "evidence": "Named in its strategy",
                            "source_ids": ["S1"]},
                           {"priority": "Measurable outcomes", "evidence": "Grantees report results each year",
                            "source_ids": ["S1"]},
                           {"priority": "Community voice", "evidence": "Asks how participants shape programs",
                            "source_ids": []}],
            "funding_areas": ["Housing", "Family economic security"], "typical_grant": None,
            "language": ["housing stability", "family well-being"],
            "evaluation_expectations": ["Annual outcome report"], "cautions": ["No capital campaigns"],
            "sources": [{"id": "S1", "title": f"{name}: our strategy", "publisher": name, "url": None,
                         "note": "Describes its funding priorities.", "verified": False}]}


def _grant_draft(messages: list[ModelMessage]) -> dict:
    """Scripted Grant Writer: one answer per pasted question, using live number tokens."""
    data = _prompt_json(messages)
    lines = [q.strip() for q in (data.get("questions_from_staff") or "").splitlines() if q.strip()]
    lines = lines or ["Organization background", "Program description", "Outcomes and evaluation"]
    keys = {n["key"] for n in data.get("organization", {}).get("numbers", [])}
    stat = "{{top_improvement}} of matched families improved" if "top_improvement" in keys else "families are improving"
    answers = [{"question": q, "word_limit": None,
                "answer": f"We have enrolled {{{{participants}}}} families, and {stat}. "
                          "[ADD: total program budget for the grant period]",
                "priorities_addressed": ["Housing stability for families with children"], "source_ids": ["S1"]}
               for q in lines]
    return {"title": f"Application to {data.get('foundation_profile', {}).get('foundation', 'the foundation')}",
            "opportunity": data.get("opportunity") or "", "answers": answers,
            "fit_summary": "Our program keeps families housed, which is the foundation's first priority. "
                           "{{matched}} families answered both our pre and post surveys.",
            "checklist": [{"item": "Logic model", "status": "ready", "note": "From the Studio."},
                          {"item": "Program budget", "status": "needs_input", "note": "Add the line-item budget."}],
            "needs_input": ["Total program budget", "Board list"]}


async def scripted(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    await asyncio.sleep(1.2)  # slow enough to watch the huddle
    out = info.output_tools[0]
    title = out.parameters_json_schema.get("title", "")
    if title in ("SpecialistAdvice", "SpecialistQuestions", "SpecialistReview"):
        args = _specialist(title, _who(messages))
    elif title == "SurveyReviewResult":
        args = _survey_review(messages)
    elif title == "ReportDraft":
        args = _report_draft(messages)
    elif title == "PrivacyReview":
        args = {"clean": True, "findings": [], "summary": "No names, contact details, or small groups found."}
    elif title == "FoundationProfile":
        args = _foundation(messages)
    elif title == "GrantDraft":
        args = _grant_draft(messages)
    else:
        args = CANNED[title]
    return ModelResponse(parts=[ToolCallPart(out.name, args)])


common.MODEL_OVERRIDE = FunctionModel(scripted, model_name="scripted-demo")

if __name__ == "__main__":
    import main

    print(f"Demo backend (scripted agents, no API calls). Temp data: {_tmp}")
    uvicorn.run(main.app, host="127.0.0.1", port=8000)
