"""Who is calling? FastAPI dependencies that every protected route uses."""

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from db import Organization, Participant, StaffUser, get_db
from security import DEMO_READ_ONLY, PARTICIPANT_COOKIE, STAFF_COOKIE, is_demo, read_token


@dataclass
class StaffCtx:
    user: StaffUser
    org: Organization
    db: Session


@dataclass
class ParticipantCtx:
    participant: Participant
    org: Organization
    db: Session


def current_staff(request: Request, db: Session = Depends(get_db)) -> StaffCtx:
    claims = read_token(request.cookies.get(STAFF_COOKIE), "staff")
    user = db.get(StaffUser, int(claims["sub"])) if claims else None
    if not user or user.org_id != claims.get("org"):
        raise HTTPException(401, "Please sign in.")
    if request.method not in ("GET", "HEAD") and is_demo(user.username_hash):
        raise HTTPException(403, DEMO_READ_ONLY)
    return StaffCtx(user=user, org=db.get(Organization, user.org_id), db=db)


def current_participant(request: Request, db: Session = Depends(get_db)) -> ParticipantCtx:
    claims = read_token(request.cookies.get(PARTICIPANT_COOKIE), "participant")
    p = db.get(Participant, int(claims["sub"])) if claims else None
    if not p or not p.active or p.org_id != claims.get("org"):
        raise HTTPException(401, "Please sign in with your code and PIN.")
    return ParticipantCtx(participant=p, org=db.get(Organization, p.org_id), db=db)
