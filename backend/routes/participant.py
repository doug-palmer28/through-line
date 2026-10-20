"""Participant portal: a participant (signed in with code + PIN) sees and answers their surveys.

Participants only ever see published participant surveys from their own organization,
and only their own submission status. They can't see any other answers, and
each pre or post survey can be submitted once.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select

import surveys
from audit import audit_append
from db import Instrument, Response
from deps import ParticipantCtx, current_participant

router = APIRouter(prefix="/api/participant", tags=["participant portal"])


def _published(ctx: ParticipantCtx):
    return ctx.db.exec(select(Instrument).where(Instrument.org_id == ctx.org.id, Instrument.status == "published",
                                                Instrument.method == "participant_survey")).all()


def _done(ctx: ParticipantCtx, instrument_id: int) -> set[str]:
    return set(ctx.db.exec(select(Response.wave).where(Response.instrument_id == instrument_id,
                                                       Response.participant_id == ctx.participant.id)).all())


@router.get("/surveys")
def my_surveys(ctx: ParticipantCtx = Depends(current_participant)):
    out = []
    for inst in _published(ctx):
        done = _done(ctx, inst.id)
        waves = [w for w in surveys.WAVES if surveys.questions_for(inst.questions, w)]
        out.append({"id": inst.id, "name": inst.name, "waves": [{"wave": w, "done": w in done} for w in waves]})
    return {"code": ctx.participant.code, "org_name": ctx.org.name, "surveys": out}


def _instrument(ctx: ParticipantCtx, instrument_id: int) -> Instrument:
    inst = next((i for i in _published(ctx) if i.id == instrument_id), None)
    if not inst:
        raise HTTPException(404, "That survey isn't available.")
    return inst


@router.get("/surveys/{instrument_id}/{wave}")
def survey_form(instrument_id: int, wave: str, ctx: ParticipantCtx = Depends(current_participant)):
    if wave not in surveys.WAVES:
        raise HTTPException(404, "Unknown survey.")
    inst = _instrument(ctx, instrument_id)
    if wave in _done(ctx, inst.id):
        raise HTTPException(409, "You've already completed this survey. Thank you!")
    qs = surveys.questions_for(inst.questions, wave)
    show_demo = wave == "pre" or "pre" not in _done(ctx, inst.id)
    return {
        "name": inst.name, "wave": wave,
        "questions": [{"id": q["id"], "text": q["text"], "scale": q["scale"],
                       "options": q.get("options") if q["scale"] in surveys.CHOICE else surveys.SCALES[q["scale"]]["options"]}
                      for q in qs],
        "demographics": [{"key": k, **{f: surveys.DEMOGRAPHICS[k][f] for f in ("label", "options", "multi")}}
                         for k in inst.demographics] if show_demo else [],
    }


class SubmitIn(BaseModel):
    answers: dict = {}
    demographics: dict = {}


@router.post("/surveys/{instrument_id}/{wave}")
def submit(instrument_id: int, wave: str, body: SubmitIn, ctx: ParticipantCtx = Depends(current_participant)):
    if wave not in surveys.WAVES:
        raise HTTPException(404, "Unknown survey.")
    inst = _instrument(ctx, instrument_id)
    if wave in _done(ctx, inst.id):
        raise HTTPException(409, "You've already completed this survey. Thank you!")
    try:
        answers = surveys.clean_answers(inst.questions, wave, body.answers)
        demo = surveys.clean_demographics(inst.demographics, body.demographics)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not answers:
        raise HTTPException(400, "Please answer at least one question.")
    ctx.db.add(Response(org_id=ctx.org.id, instrument_id=inst.id, participant_id=ctx.participant.id, wave=wave,
                        answers=answers, demographics=demo, entered_by="participant"))
    ctx.db.commit()
    audit_append(event="survey_submitted", agent="human", team="data_collection",
                 human={"role": "participant", "action": "submitted_survey", "org_id": ctx.org.id},
                 output={"instrument_id": inst.id, "wave": wave, "answers": len(answers)})
    return {"ok": True}
