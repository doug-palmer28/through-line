"""Data types for Through Line.

Agent outputs are Pydantic models so every agent returns structured, checkable
data rather than free text. Field descriptions are sent to the model as part of
the output schema, so they double as instructions.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Specialist = Literal["evaluation_specialist", "client_advocate", "sector_expert", "funder_researcher"]

INTERVIEW_QUESTIONS = 5  # The interview is always exactly five questions.
ANSWER_WORD_LIMIT = 200  # per answer; the UI counts down
FEEDBACK_WORD_LIMIT = 150

UPLOAD_REQUEST_HELP = (
    "Optional. Only if a specific existing document would clearly help (e.g. 'your most recent annual report' or "
    "'any survey you already use'), name it in one short sentence. Otherwise null. The client may skip it."
)


def word_count(text: str) -> int:
    return len(text.split())


# ============================================================ what the team knows about the org


class SuggestedQuestion(BaseModel):
    question: str = Field(description="A plain-language interview question for the client.")
    why: str = Field(description="One sentence: what it would help the team learn.")


class OrgSnapshot(BaseModel):
    """What the team has learned about the nonprofit. Built at intake, refined during the interview."""

    org_name: str
    sector: str = Field(description="Plain-language field of work, e.g. 'homelessness services', 'youth financial literacy'.")
    mission: str = Field(description="The mission in one or two sentences, in the org's own words where possible.")
    populations_served: list[str] = Field(default_factory=list, description="Who the program serves (groups, not individuals).")
    programs: list[str] = Field(default_factory=list, description="Named programs or services.")
    activities: list[str] = Field(default_factory=list, description="What staff and volunteers actually do.")
    resources: list[str] = Field(default_factory=list, description="Staff, funding, partners, facilities mentioned.")
    outcomes_claimed: list[str] = Field(default_factory=list, description="Changes the org says it creates.")
    existing_measures: list[str] = Field(default_factory=list, description="Anything the org already tracks.")
    gaps: list[str] = Field(default_factory=list, description="Important things still unknown, most important first.")


class SectorBrief(BaseModel):
    """The Sector Expert's working knowledge base for this org's field. Lives only in the session."""

    suggested_questions: list[SuggestedQuestion] = Field(default_factory=list, description="1-2 interview questions a practitioner in this field would ask.")
    sector: str
    common_outcomes: list[str] = Field(description="Outcomes programs in this field usually aim for, short to long term.")
    best_practices: list[str] = Field(description="Widely recognized practices or program models in this field.")
    standards_and_frameworks: list[str] = Field(description="Named standards, frameworks, or funder expectations (e.g. Housing First, HUD outcome measures).")
    common_metrics: list[str] = Field(description="Indicators organizations in this field typically track.")
    pitfalls: list[str] = Field(description="Common mistakes when small orgs in this field describe their impact.")
    caveat: str = Field(description="One sentence noting this brief comes from general knowledge, not verified sources.")


class Citation(BaseModel):
    """A source the team relied on. `verified` is set by code, never by the model."""

    id: str = Field(description="Short id used to cite it, e.g. 'S1', 'S2'.")
    title: str = Field(description="Title of the page, report, or framework.")
    publisher: str = Field(description="Who published it, e.g. 'U.S. Department of Housing and Urban Development'.")
    url: str | None = Field(default=None, description="Exact URL from your search results. Null if you didn't open it in a search.")
    note: str = Field(description="One sentence: what this source says that matters here.")
    verified: bool = Field(default=False, description="Leave false. Set by the system if the URL came from a live web search.")


class FunderPriority(BaseModel):
    funder: str = Field(description="A named funder or funder type, e.g. 'HUD Continuum of Care', 'community foundations'.")
    funder_type: Literal["government", "philanthropic", "both"]
    what_they_want: str = Field(description="What they ask grantees to measure or report, in one or two sentences.")
    source_ids: list[str] = Field(default_factory=list)


class PeerModel(BaseModel):
    organization: str = Field(description="A well-regarded organization or network in this field.")
    how_they_frame_it: str = Field(description="How they describe their outcomes or logic model, in one or two sentences.")
    source_ids: list[str] = Field(default_factory=list)


class FieldResearch(BaseModel):
    """The Funder Researcher's brief: what funders in this field want, and how leading organizations frame it."""

    funder_priorities: list[FunderPriority] = Field(description="3-6 funders or funder types and what they want measured.")
    compelling_metrics: list[str] = Field(description="3-6 metrics funders in this field find most compelling, with source ids in brackets.")
    peer_models: list[PeerModel] = Field(description="2-4 leading organizations/networks and how they frame outcomes.")
    framing_tips: list[str] = Field(description="2-4 tips for presenting this kind of program to funders.")
    suggested_questions: list[SuggestedQuestion] = Field(description="1-2 interview questions that would help align with funders.")
    sources: list[Citation] = Field(description="Every source cited above, with ids S1, S2, ...")


class MeasureSuggestion(BaseModel):
    outcome: str = Field(description="The approved logic model outcome this measure fits (copy its wording).")
    measure: str = Field(description="The measure or indicator, e.g. 'Housing retention at 12 months'.")
    sample_questions: list[str] = Field(description="2-4 question items used for this measure in the field (adapted to plain language).")
    who_uses_it: str = Field(description="Which funders or organizations use or require it.")
    source_ids: list[str] = Field(default_factory=list)


class MetricsResearch(BaseModel):
    """The Funder Researcher's evidence for the measurement plan."""

    suggestions: list[MeasureSuggestion] = Field(description="4-8 measures, at least one per short-term outcome where possible.")
    sources: list[Citation] = Field(description="Every source cited, with ids S1, S2, ...")


class SpecialistQuestions(BaseModel):
    """A specialist's proposed interview questions (collected into the team's question pool)."""

    specialist: Specialist
    questions: list[SuggestedQuestion] = Field(description="1-2 questions only you would think to ask.")


class SpecialistReview(BaseModel):
    """A specialist's peer review of a draft, before the client sees it."""

    specialist: Specialist
    verdict: Literal["ready", "needs_changes"]
    keep: list[str] = Field(default_factory=list, description="At most 2 things that are working and should stay.")
    change: list[str] = Field(default_factory=list, description="At most 4 specific changes, each naming the item to change.")


class SpecialistAdvice(BaseModel):
    """A specialist's answer to the boss. Kept short on purpose."""

    specialist: Specialist
    summary: str = Field(description="Your answer in two or three sentences.")
    recommendations: list[str] = Field(default_factory=list, description="At most 4 concrete recommendations.")
    concerns: list[str] = Field(default_factory=list, description="At most 3 risks or things that don't add up.")
    suggested_question: str | None = Field(default=None, description="A question you'd want asked of the client, if any.")


# ============================================================ the logic model


class LogicModel(BaseModel):
    """A simple logic model. Each list item is a short phrase, not a paragraph."""

    program_name: str = Field(description="The program this logic model describes.")
    theory_of_change: str = Field(description="One to three sentences: 'If we ..., then ..., because ...'.")
    inputs: list[str] = Field(description="Resources: staff, funding, partners, space, volunteers.")
    activities: list[str] = Field(description="What the program does.")
    outputs: list[str] = Field(description="Direct, countable products of activities (e.g. '120 workshops held').")
    short_term_outcomes: list[str] = Field(description="Changes in knowledge, skills, attitudes, or access (months).")
    long_term_outcomes: list[str] = Field(description="Lasting changes in condition or status (a year or more).")
    assumptions: list[str] = Field(default_factory=list, description="What must be true for the model to work.")
    external_factors: list[str] = Field(default_factory=list, description="Things outside the org's control that affect results.")


# ============================================================ boss outputs, one per phase


class IntakeResult(BaseModel):
    """Boss output after reading the client's materials."""

    snapshot: OrgSnapshot
    welcome_message: str = Field(description="2-4 warm, plain sentences to the client: what you read and what you understood. No jargon.")
    upload_request: str | None = Field(default=None, description=UPLOAD_REQUEST_HELP)


class FirstQuestion(BaseModel):
    """Boss output opening the interview, after the team has proposed questions."""

    question: str = Field(description="Question 1 of 5. One question only, plain language.")
    why_we_ask: str = Field(description="One sentence on why this question matters for the logic model.")


class InterviewTurn(BaseModel):
    """Boss output after each client answer."""

    acknowledgement: str = Field(description="1-2 sentences reflecting back what you heard.")
    learned: list[str] = Field(description="New facts from this answer, as short notes for the team.")
    next_question: str | None = Field(description="The next question, or null if this was answer 5 of 5.")
    why_we_ask: str | None = Field(default=None, description="One sentence on why the next question matters.")
    upload_request: str | None = Field(default=None, description=UPLOAD_REQUEST_HELP)


class AlignmentNote(BaseModel):
    note: str = Field(description="How one part of the logic model lines up with funder or field expectations.")
    source_ids: list[str] = Field(default_factory=list, description="Ids of the research sources behind it.")


class DraftResult(BaseModel):
    """Boss output when drafting or revising the logic model."""

    logic_model: LogicModel
    alignment: list[AlignmentNote] = Field(default_factory=list, description="2-5 notes on how the model lines up with funders and leading organizations in this field.")
    message_to_client: str = Field(description="2-4 sentences introducing the draft (or what changed) and inviting feedback.")
    team_notes: list[str] = Field(default_factory=list, description="At most 5 short notes on what each specialist contributed or flagged.")
    upload_request: str | None = Field(default=None, description=UPLOAD_REQUEST_HELP)


class DocumentNotes(BaseModel):
    """Boss output after reading an extra document the client uploaded mid-session."""

    notes: list[str] = Field(description="New, relevant facts from the document, as short notes for the team (at most 8).")
    acknowledgement: str = Field(description="1-2 sentences thanking the client and naming what was useful.")


# ============================================================ the measurement plan

Scale = Literal["agree_5", "confidence_5", "frequency_5", "scale_0_10", "yes_no", "number", "open_text"]
Method = Literal["participant_survey", "staff_assessment", "program_records"]


class SurveyQuestion(BaseModel):
    text: str = Field(description="The exact question wording, in plain language at about a 6th-grade reading level.")
    scale: Scale = Field(description=(
        "agree_5: Strongly disagree..Strongly agree. confidence_5: Not at all..Extremely confident. "
        "frequency_5: Never..Always. scale_0_10: 0-10 rating. yes_no. number: a count. open_text: a short written answer."))
    included: bool = Field(default=True, description="True for the questions you recommend using; false for optional extras the client can switch on.")
    note: str | None = Field(default=None, description="Optional: who uses or requires this item, e.g. 'HUD asks this at program exit'.")
    source_ids: list[str] = Field(default_factory=list, description="Ids of research sources behind this question.")


class Metric(BaseModel):
    name: str = Field(description="Short name, e.g. 'Budgeting confidence'.")
    outcome: str = Field(description="The logic model outcome this metric shows progress on (copy its wording).")
    method: Method
    questions: list[SurveyQuestion] = Field(description="3-5 candidate questions: 2-3 recommended (included=true) plus 1-2 optional extras (included=false). For program_records, describe each record to pull as a 'number' question.")
    timing: str = Field(description="When it's collected, e.g. 'Pre (first session) and post (week 12)'.")
    how_scored: str = Field(description="How the number is calculated, e.g. '% of participants whose score rises by 1+ point'.")
    why_it_matters: str = Field(description="One sentence a funder would understand.")
    funder_relevance: str = Field(default="", description="Which funders ask for this (or similar) and why, citing source ids in brackets.")
    source_ids: list[str] = Field(default_factory=list, description="Ids of research sources behind this metric.")


class CollectionTool(BaseModel):
    name: str = Field(description="e.g. 'Participant check-in survey'.")
    method: Method
    when: str = Field(description="When and how it is given, e.g. 'On paper or phone at intake and at exit'.")
    metrics: list[str] = Field(description="Names of the metrics this tool collects.")


class MeasurementPlan(BaseModel):
    summary: str = Field(description="2-3 sentences describing the plan in plain language.")
    metrics: list[Metric] = Field(description="The top 3-5 metrics, most important first.")
    tools: list[CollectionTool] = Field(description="1-2 data-collection tools that together cover every metric.")
    sources: list[Citation] = Field(default_factory=list, description="Copy every research source you cite, keeping its id, title, publisher, url and note.")


class MetricsResult(BaseModel):
    """Boss output when proposing or revising the measurement plan."""

    plan: MeasurementPlan
    message_to_client: str = Field(description="2-4 sentences introducing the plan (or what changed) and inviting feedback.")
    team_notes: list[str] = Field(default_factory=list, description="At most 5 short notes on what each specialist contributed or flagged.")


# ============================================================ API request bodies


class AnswerIn(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)

    @field_validator("answer")
    @classmethod
    def _limit(cls, v: str) -> str:
        if word_count(v) > ANSWER_WORD_LIMIT:
            raise ValueError(f"Please keep answers to {ANSWER_WORD_LIMIT} words.")
        return v


class FeedbackIn(BaseModel):
    feedback: str = Field(min_length=1, max_length=4000)

    @field_validator("feedback")
    @classmethod
    def _limit(cls, v: str) -> str:
        if word_count(v) > FEEDBACK_WORD_LIMIT:
            raise ValueError(f"Please keep feedback to {FEEDBACK_WORD_LIMIT} words.")
        return v


# ============================================================ audit log


class ToolCallRecord(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)
    result_summary: str | None = None


class AuditEntry(BaseModel):
    """One line of output/audit_log.json. `seq`, `prev_hash` and `hash` are filled by the writer."""

    seq: int
    prev_hash: str
    logged_at: str
    event: str
    run_id: str | None = None
    session_id: str | None = None
    step_id: str | None = None
    parent_step_id: str | None = None
    team: str | None = "logic_model_studio"
    phase: str | None = None
    agent: str | None = None
    model: str | None = None
    prompt_file: str | None = None
    prompt_hash: str | None = None
    input_summary: str | None = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    output: Any = None
    usage: dict[str, int] | None = None
    human: dict[str, Any] | None = None
    error: str | None = None


# ============================================================ Survey Review Bot


class SurveyFix(BaseModel):
    """A change staff can apply with one click."""

    action: Literal["rewrite", "change_scale", "hide", "set_waves", "set_reverse", "add_open_question"]
    text: str | None = Field(default=None, description="New wording (rewrite) or the new question (add_open_question).")
    scale: Scale | None = Field(default=None, description="New scale (change_scale).")
    waves: list[Literal["pre", "post"]] | None = Field(default=None, description="When to ask (set_waves).")
    reverse: bool | None = Field(default=None, description="Mark as reverse-scored (set_reverse).")


class SurveyIssue(BaseModel):
    question_id: str | None = Field(description="The id of the question this is about, or null for the whole survey.")
    kind: Literal["wording", "scale_consistency", "insight", "burden", "sensitivity", "missing"]
    severity: Literal["high", "medium", "low"]
    problem: str = Field(description="One sentence, plain language.")
    suggestion: str = Field(description="One sentence: what to do.")
    fix: SurveyFix | None = Field(default=None, description="A concrete one-click change, if there is one.")


class SurveyReviewResult(BaseModel):
    summary: str = Field(description="2-3 sentences: is this survey ready, and what matters most.")
    ready: bool = Field(description="True if it can be sent as is (minor issues only).")
    strengths: list[str] = Field(default_factory=list, description="At most 3.")
    issues: list[SurveyIssue] = Field(default_factory=list, description="At most 8, most important first.")


# ============================================================ Report Designer
#
# Numbers in the deck, flyer, and grant drafts are written as {{key}} tokens from the
# "numbers" list the agent is given (e.g. "{{improved:housing-stability}} of families").
# The app fills them in from the latest data every time the files are viewed or downloaded,
# so the report "shell" stays current as more surveys come in, with no new AI call.

NUMBER_TOKEN_HELP = "Write every number from the data as its {{key}} token from the numbers list, e.g. '{{participants}}'."


SlideLayout = Literal["title", "statement", "story", "stats", "chart", "logic", "quote", "ask", "closing"]


class Stat(BaseModel):
    value: str = Field(description="One {{key}} token from the numbers list, e.g. '{{participants}}'. Never a typed number.")
    label: str = Field(description="What it means, in 3-8 words.")


class DeckSlide(BaseModel):
    layout: SlideLayout = Field(description=(
        "title: cover. statement: one big sentence. story: headline + 2-4 short bullets. stats: up to 3 big numbers. "
        "chart: one chart by chart_id + a takeaway. logic: the theory of change as a pathway. quote: one participant quote. "
        "ask: what support would make possible. closing: thank you + contact."))
    headline: str = Field(description="Short, active headline (max ~10 words).")
    body: list[str] = Field(default_factory=list, description="0-4 short lines (story/ask/logic); for chart slides, 1 takeaway sentence.")
    stats: list[Stat] = Field(default_factory=list, description="For 'stats' slides only: 2-3 numbers from the data.")
    chart_id: str | None = Field(default=None, description="For 'chart' slides only: one of the chart ids provided.")
    quote: str | None = Field(default=None, description="For 'quote' slides only: a provided participant quote, unchanged.")
    speaker_notes: str = Field(description="What to say: about 60-90 seconds of plain spoken language. " + NUMBER_TOKEN_HELP)


class OnePager(BaseModel):
    headline: str = Field(description="Flyer headline, max ~8 words.")
    subhead: str = Field(description="One sentence about the organization and who it serves.")
    stats: list[Stat] = Field(description="3-4 headline numbers from the data.")
    story: str = Field(description="2-3 sentences: the change the program creates, grounded in the data.")
    chart_ids: list[str] = Field(default_factory=list, description="0-2 chart ids to show on the flyer.")
    quote: str | None = Field(default=None, description="Optional: one provided participant quote, unchanged.")
    call_to_action: str = Field(description="One sentence inviting support.")


class DesignChoices(BaseModel):
    """The agent's reading of the org's design standards, turned into concrete settings."""

    primary: str = Field(description="Hex color, e.g. '#1F4E5F'. Use the org's colors if given.")
    secondary: str = Field(description="Hex color for the second data series and accents.")
    accent: str = Field(description="Hex color for highlights (one key number per slide at most).")
    background: str = Field(description="Hex background color: white or a very light tint.")
    heading_font: str = Field(description="A widely installed font: Georgia, Calibri, Arial, Segoe UI, Century Gothic, Garamond, Trebuchet MS, Verdana.")
    body_font: str = Field(description="A widely installed font from the same list.")
    mood: str = Field(description="One line describing the visual mood, e.g. 'warm, hopeful, plain-spoken'.")


class ReportDraft(BaseModel):
    deck_title: str
    deck_subtitle: str
    slides: list[DeckSlide] = Field(description="10-14 slides for a 10-15 minute talk, in order.")
    one_pager: OnePager
    design: DesignChoices


class PrivacyFinding(BaseModel):
    where: str = Field(description="Which slide/field, e.g. 'slide 6 quote' or 'one-pager story'.")
    text: str = Field(description="The exact problematic text as it appears.")
    issue: str = Field(description="Why it could identify someone (name, address, tiny group, specific detail…).")
    replacement: str = Field(description="Safe replacement text (may be empty to remove it).")


class PrivacyReview(BaseModel):
    clean: bool = Field(description="True if nothing could identify a participant or staff member.")
    findings: list[PrivacyFinding] = Field(default_factory=list)
    summary: str = Field(description="One sentence for the staff member.")


# ============================================================ Grant Writer


class FoundationPriority(BaseModel):
    priority: str = Field(description="What the foundation cares about, in its own words where possible.")
    evidence: str = Field(description="Where this shows up (mission statement, past grants, RFP section…).")
    source_ids: list[str] = Field(default_factory=list, description="Ids of the sources that support it, e.g. ['S1'].")


class FoundationProfile(BaseModel):
    """The Funder Researcher's read on one foundation."""

    foundation: str
    mission: str = Field(description="The foundation's mission in 1-2 sentences.")
    priorities: list[FoundationPriority] = Field(description="3-6 things this foundation clearly values, most important first.")
    funding_areas: list[str] = Field(default_factory=list, description="Program areas / geographies it funds.")
    typical_grant: str | None = Field(default=None, description="Typical grant size or range, only if a source states it.")
    language: list[str] = Field(default_factory=list, description="2-6 words or phrases the foundation uses that an applicant should echo honestly.")
    evaluation_expectations: list[str] = Field(default_factory=list, description="What it asks grantees to measure or report.")
    cautions: list[str] = Field(default_factory=list, description="Eligibility limits or things it does not fund.")
    sources: list[Citation] = Field(description="Every source cited, ids S1, S2, ...")


class GrantAnswer(BaseModel):
    question: str = Field(description="The foundation's question or required section, as written.")
    word_limit: int | None = Field(default=None, description="The limit if the foundation states one, else null.")
    answer: str = Field(description="The draft answer, in the organization's voice. " + NUMBER_TOKEN_HELP)
    priorities_addressed: list[str] = Field(default_factory=list, description="Which foundation priorities this answer speaks to.")
    source_ids: list[str] = Field(default_factory=list, description="Foundation sources this answer leans on.")


class ChecklistItem(BaseModel):
    item: str = Field(description="A requested attachment or piece of information (budget, 990, board list…).")
    status: Literal["ready", "needs_input"] = Field(description="'ready' only if the app's data covers it; otherwise 'needs_input'.")
    note: str = Field(default="", description="What staff need to supply or check.")


class GrantDraft(BaseModel):
    title: str = Field(description="e.g. 'Application to the X Foundation: Family Stability Fund'.")
    opportunity: str = Field(default="", description="Program or RFP name, deadline, and amount if stated.")
    fit_summary: str = Field(description="3-4 sentences: why this organization fits this foundation's priorities. " + NUMBER_TOKEN_HELP)
    answers: list[GrantAnswer] = Field(description="One per question/section, in the foundation's order.")
    checklist: list[ChecklistItem] = Field(default_factory=list, description="Attachments and facts the foundation asks for.")
    needs_input: list[str] = Field(default_factory=list, description="Facts the draft needs but the data doesn't have (budget, staff names, dates…). Never invent them.")
