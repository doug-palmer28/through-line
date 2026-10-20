"""Logic Model Studio: the client builds a logic model and measurement plan with Agent Team 1.

Flow: start (read uploads) -> intake -> 5 interview answers -> draft -> edit / feedback -> approve
      -> metrics -> edit / feedback -> approve -> download.
The frontend polls /feed while the team is working to show the live huddle.
"""

import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

import allowances
import sessions
from agents import team
from audit import audit_append, audit_entries, audit_verify
from config import MODEL_NAME
from deps import StaffCtx, current_staff
from intake import MAX_FILES, IntakeError, fetch_website, read_upload_files
from models import ANSWER_WORD_LIMIT, FEEDBACK_WORD_LIMIT, AnswerIn, FeedbackIn, LogicModel, MeasurementPlan
from pptx_io import build_deck

router = APIRouter(prefix="/api/logic-model", tags=["logic model"])

LOGIC_MODEL_STAGES = [
    {"key": "inputs", "label": "Inputs", "hint": "Resources the program relies on"},
    {"key": "activities", "label": "Activities", "hint": "What the program does"},
    {"key": "outputs", "label": "Outputs", "hint": "Direct, countable products of activities"},
    {"key": "short_term_outcomes", "label": "Short-term outcomes", "hint": "Changes in knowledge, skills, attitudes"},
    {"key": "long_term_outcomes", "label": "Long-term outcomes", "hint": "Lasting changes in condition or status"},
]

AGENT_TEAM = [
    {"key": "boss", "name": "Team Lead", "role": "Talks with you, asks the questions, and writes the drafts"},
    {"key": "sector_expert", "name": "Sector Expert", "role": "Knows best practices and standards in your field"},
    {"key": "funder_researcher", "name": "Funder Researcher", "role": "Researches what funders in your field want to see, with sources"},
    {"key": "client_advocate", "name": "Client Advocate", "role": "Keeps it in your words, at your real capacity"},
    {"key": "evaluation_specialist", "name": "Evaluation Specialist", "role": "Checks that the logic holds and can be measured"},
]


@router.get("")
def overview():  # public: just the stage names and team roster
    return {
        "stages": LOGIC_MODEL_STAGES,
        "agent_team": [{**a, "model": MODEL_NAME} for a in AGENT_TEAM],
        "limits": {"answer_words": ANSWER_WORD_LIMIT, "feedback_words": FEEDBACK_WORD_LIMIT},
    }


# ============================================================ helpers


def _session(session_id: str, ctx: StaffCtx) -> sessions.Session:
    session = sessions.get(session_id)
    if not session or session.org_id != ctx.org.id:  # only your own organization's session
        raise HTTPException(404, "This session has ended. Start a new one.")
    session.actor_id = ctx.user.id  # token ledger: whoever is clicking now
    return session


async def _run(coro):
    """Turn agent/phase errors into clear HTTP errors."""
    try:
        return await coro
    except team.PhaseError as exc:
        raise HTTPException(409, str(exc)) from exc
    except RuntimeError as exc:
        if "PORTKEY_API_KEY" in str(exc):
            raise HTTPException(503, "The AI service isn't configured on the server.") from exc
        raise HTTPException(502, "The agent team hit a problem. Please try again.") from exc
    except Exception as exc:
        raise HTTPException(502, "The agent team hit a problem. Please try again.") from exc


def _sync(fn, *args):
    try:
        fn(*args)
    except team.PhaseError as exc:
        raise HTTPException(409, str(exc)) from exc


# ============================================================ start + intake


@router.post("/sessions")
async def start_session(
    org_name: str = Form(..., min_length=1, max_length=120),
    website_url: str | None = Form(None),
    files: list[UploadFile] = File(default=[]),
    ctx: StaffCtx = Depends(current_staff),
):
    """Read uploads + website in memory and open a session. The team starts with POST /intake."""
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Please upload at most {MAX_FILES} files.")
    try:
        sources = await read_upload_files(files)
        if website_url and website_url.strip():
            sources.append(await fetch_website(website_url))
    except IntakeError as exc:
        raise HTTPException(400, str(exc)) from exc

    allowances.claim(ctx.db, ctx.org, "studio_starts",
                     f"Your organization has used its {allowances.STUDIO_STARTS} Studio sessions. "
                     "Contact Through Line if you need another.")
    session = sessions.create(org_name, org_id=ctx.org.id)
    session.actor_id = ctx.user.id
    ctx.org.studio_session_id = session.id
    ctx.db.add(ctx.org)
    ctx.db.commit()
    session.pending_sources = sources
    session.source_manifest = [s.manifest() for s in sources]
    session.save()
    audit_append(event="session_started", session_id=session.id, phase="intake", agent="human",
                 human={"role": "client", "action": "started_session"},
                 input_summary=f"{len(files)} file(s), website: {'yes' if website_url else 'no'}")
    return session.view()


@router.post("/sessions/{session_id}/intake")
async def intake(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        await _run(team.run_intake(session))
    return session.view()


@router.get("/sessions/{session_id}")
def get_session(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    return _session(session_id, ctx).view()


@router.get("/sessions/{session_id}/feed")
def feed(session_id: str, after: int = 0, ctx: StaffCtx = Depends(current_staff)):
    """Live team activity since `after` (no lock: readable while the team is working)."""
    session = _session(session_id, ctx)
    return {"events": [e for e in session.feed if e["seq"] > after], "phase": session.phase}


# ============================================================ interview + extra documents


@router.post("/sessions/{session_id}/answer")
async def answer(session_id: str, body: AnswerIn, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        await _run(team.answer_question(session, body.answer))
    return session.view()


@router.post("/sessions/{session_id}/documents")
async def add_document(session_id: str, file: UploadFile = File(...), ctx: StaffCtx = Depends(current_staff)):
    """An optional extra document (often one the team asked for). Read in memory, never saved."""
    session = _session(session_id, ctx)
    try:
        [source] = await read_upload_files([file], start=len(session.source_manifest) + 1)
    except IntakeError as exc:
        raise HTTPException(400, str(exc)) from exc
    manifest = source.manifest()
    async with session.lock:
        await _run(team.absorb_document(session, source))
        session.source_manifest.append(manifest)
        session.save()
    return session.view()


@router.post("/sessions/{session_id}/skip-upload")
def skip_upload(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    team.skip_upload(session)
    return session.view()


# ============================================================ logic model


@router.post("/sessions/{session_id}/draft")
async def draft(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        await _run(team.draft_logic_model(session))
    return session.view()


@router.post("/sessions/{session_id}/feedback")
async def feedback(session_id: str, body: FeedbackIn, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        await _run(team.revise_logic_model(session, body.feedback))
    return session.view()


@router.put("/sessions/{session_id}/logic-model")
async def edit_logic_model(session_id: str, body: LogicModel, ctx: StaffCtx = Depends(current_staff)):
    """Save the client's direct edits as a new draft version."""
    session = _session(session_id, ctx)
    async with session.lock:
        _sync(team.save_logic_model_edit, session, body)
    return session.view()


@router.post("/sessions/{session_id}/approve")
async def approve(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        _sync(team.approve_logic_model, session)
    return session.view()


# ============================================================ measurement plan


@router.post("/sessions/{session_id}/metrics/draft")
async def draft_metrics(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        await _run(team.draft_metrics(session))
    return session.view()


@router.post("/sessions/{session_id}/metrics/feedback")
async def metrics_feedback(session_id: str, body: FeedbackIn, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        await _run(team.revise_metrics(session, body.feedback))
    return session.view()


@router.put("/sessions/{session_id}/metrics")
async def edit_metrics(session_id: str, body: MeasurementPlan, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        _sync(team.save_plan_edit, session, body)
    return session.view()


@router.post("/sessions/{session_id}/metrics/approve")
async def approve_metrics(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    async with session.lock:
        _sync(team.approve_plan, session)
        ctx.org.logic_model = session.approved.model_dump() if session.approved else None
        ctx.org.measurement_plan = session.approved_plan.model_dump() if session.approved_plan else None
        ctx.db.add(ctx.org)
        ctx.db.commit()
    return session.view()


# ============================================================ download, end, audit


@router.get("/sessions/{session_id}/export.pptx")
def export_pptx(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    session = _session(session_id, ctx)
    model = session.approved or session.current_draft
    if not model:
        raise HTTPException(409, "There's no logic model to download yet.")
    plan = session.approved_plan or session.current_plan
    version = session.drafts[-1]["version"]
    latest = session.drafts[-1]
    data = build_deck(model, session.org_name, version, plan,
                      alignment=latest.get("alignment"), sources=latest.get("sources"))
    audit_append(event="export_created", session_id=session.id, phase=session.phase, agent="human",
                 human={"role": "client", "action": "downloaded_pptx"},
                 output={"draft_version": version, "includes_plan": plan is not None})
    slug = re.sub(r"[^A-Za-z0-9]+", "_", session.org_name).strip("_")[:40] or "logic_model"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{slug}_logic_model.pptx"'},
    )


@router.delete("/sessions/{session_id}")
def end_session(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    """End the session: working notes are wiped from memory and disk."""
    _session(session_id, ctx)
    ended = sessions.end(session_id)
    if ctx.org.studio_session_id == session_id:
        ctx.org.studio_session_id = None
        ctx.db.add(ctx.org)
        ctx.db.commit()
    if ended:
        audit_append(event="session_ended", session_id=session_id, agent="human",
                     human={"role": "client", "action": "ended_session"},
                     input_summary="working notes wiped from memory and disk")
    return {"ended": ended}


@router.get("/sessions/{session_id}/audit")
def session_audit(session_id: str, ctx: StaffCtx = Depends(current_staff)):
    """The audit trail for this session, plus whether the whole log's hash chain is intact."""
    return {"verify": audit_verify(), "entries": audit_entries(session_id=session_id)}
