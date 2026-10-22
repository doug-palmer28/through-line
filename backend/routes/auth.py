"""Sign up, sign in, and sign out, for staff and for participants (two separate portals)."""

import hmac
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select

from audit import audit_append
from config import signup_code
from db import Organization, Participant, StaffUser, get_db
from deps import ParticipantCtx, StaffCtx, current_participant, current_staff
from security import (
    DEMO_USERNAME, PARTICIPANT_COOKIE, PARTICIPANT_TTL, STAFF_COOKIE, STAFF_TTL, burn_time, clear_failures, cookie_args,
    hash_secret, is_demo, locked, make_token, new_invite_code, record_failure, token_hash, username_hash, verify_secret,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
GENERIC_FAIL = "That username and password don't match."
LOCKED = "Too many attempts. Please wait 15 minutes and try again."


class SignupIn(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=10, max_length=200)
    display_name: str = Field(min_length=1, max_length=80)
    org_name: str | None = Field(default=None, max_length=120)  # create a new organization...
    invite_code: str | None = Field(default=None, max_length=40)  # ...or join one
    access_code: str | None = Field(default=None, max_length=100)  # required to start an org when the server sets one

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", v.strip()):
            raise ValueError("Usernames can use letters, numbers, dots, dashes and underscores.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if v.lower() == v or not re.search(r"\d", v):
            raise ValueError("Use at least 10 characters, including a capital letter and a number.")
        return v


class LoginIn(BaseModel):
    username: str = Field(max_length=40)
    password: str = Field(max_length=200)


class ParticipantLoginIn(BaseModel):
    code: str = Field(max_length=20)
    pin: str = Field(max_length=12)


def _me(ctx: StaffCtx) -> dict:
    return {
        "user": {"display_name": ctx.user.display_name, "role": ctx.user.role},
        "org": {"id": ctx.org.id, "name": ctx.org.name},
        "studio_session_id": ctx.org.studio_session_id,
        "has_plan": ctx.org.measurement_plan is not None,
        "demo": is_demo(ctx.user.username_hash),  # the shared, view-only example account
    }


def _sign_in(response: Response, user: StaffUser) -> None:
    token = make_token(role="staff", subject=user.id, org_id=user.org_id, ttl=STAFF_TTL)
    response.set_cookie(STAFF_COOKIE, token, **cookie_args(STAFF_TTL))


# ============================================================ staff


@router.post("/signup")
def signup(body: SignupIn, response: Response, db: Session = Depends(get_db)):
    uhash = username_hash(body.username)
    if db.exec(select(StaffUser).where(StaffUser.username_hash == uhash)).first():
        raise HTTPException(409, "That username is taken.")

    if body.invite_code:
        org = db.exec(select(Organization).where(Organization.invite_hash == token_hash(body.invite_code.strip()))).first()
        if not org or not org.invite_expires or org.invite_expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(400, "That invite code isn't valid or has expired.")
        role = "staff"
    else:
        if not body.org_name or not body.org_name.strip():
            raise HTTPException(400, "Enter your organization's name, or an invite code to join a team.")
        required = signup_code()
        if required and not hmac.compare_digest((body.access_code or "").strip().encode(), required.encode()):
            audit_append(event="signup_refused", agent="human", team="accounts", human={"role": "staff"})
            raise HTTPException(403, "Starting a new organization needs the access code from Through Line. "
                                     "To join your team, use an invite code instead.")
        org = Organization(name=body.org_name.strip())
        db.add(org)
        db.commit()
        db.refresh(org)
        role = "admin"

    user = StaffUser(org_id=org.id, username_hash=uhash, password_hash=hash_secret(body.password),
                     display_name=body.display_name.strip(), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_append(event="staff_signup", agent="human", team="accounts",
                 human={"role": role, "action": "created_account", "org_id": org.id})
    _sign_in(response, user)
    return _me(StaffCtx(user=user, org=org, db=db))


@router.post("/login")
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    ident = body.username.strip().lower()
    if ident == DEMO_USERNAME.lower():
        ident = ""  # the demo's password is public: one person's typos shouldn't lock everyone else out
    if ident and locked("staff", ident):
        raise HTTPException(429, LOCKED)
    user = db.exec(select(StaffUser).where(StaffUser.username_hash == username_hash(body.username))).first()
    if not user:
        burn_time(body.password)
    if not user or not verify_secret(user.password_hash, body.password):
        if ident:
            record_failure("staff", ident)
        audit_append(event="login_failed", agent="human", team="accounts", human={"role": "staff"})
        raise HTTPException(401, GENERIC_FAIL)
    if ident:
        clear_failures("staff", ident)
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    audit_append(event="login_success", agent="human", team="accounts",
                 human={"role": "staff", "org_id": user.org_id})
    _sign_in(response, user)
    return _me(StaffCtx(user=user, org=db.get(Organization, user.org_id), db=db))


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(STAFF_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(ctx: StaffCtx = Depends(current_staff)):
    return _me(ctx)


@router.post("/invite")
def invite(ctx: StaffCtx = Depends(current_staff)):
    """Admins create a one-time-visible invite code (valid 7 days) for a colleague to join."""
    if ctx.user.role != "admin":
        raise HTTPException(403, "Only the account that created the organization can invite staff.")
    code = new_invite_code()
    ctx.org.invite_hash = token_hash(code)
    ctx.org.invite_expires = datetime.now(timezone.utc) + timedelta(days=7)
    ctx.db.add(ctx.org)
    ctx.db.commit()
    audit_append(event="staff_invite_created", agent="human", team="accounts",
                 human={"role": "admin", "org_id": ctx.org.id})
    return {"invite_code": code, "expires_in_days": 7}


# ============================================================ participants


@router.post("/participant/login")
def participant_login(body: ParticipantLoginIn, response: Response, db: Session = Depends(get_db)):
    code = body.code.strip().upper()
    if locked("participant", code):
        raise HTTPException(429, LOCKED)
    p = db.exec(select(Participant).where(Participant.code == code, Participant.active == True)).first()  # noqa: E712
    if not p:
        burn_time(body.pin)
    if not p or not verify_secret(p.pin_hash, body.pin.strip()):
        record_failure("participant", code)
        audit_append(event="login_failed", agent="human", team="accounts", human={"role": "participant"})
        raise HTTPException(401, "That code and PIN don't match.")
    clear_failures("participant", code)
    token = make_token(role="participant", subject=p.id, org_id=p.org_id, ttl=PARTICIPANT_TTL)
    response.set_cookie(PARTICIPANT_COOKIE, token, **cookie_args(PARTICIPANT_TTL))
    org = db.get(Organization, p.org_id)
    return {"code": p.code, "org_name": org.name}


@router.post("/participant/logout")
def participant_logout(response: Response):
    response.delete_cookie(PARTICIPANT_COOKIE, path="/")
    return {"ok": True}


@router.get("/participant/me")
def participant_me(ctx: ParticipantCtx = Depends(current_participant)):
    return {"code": ctx.participant.code, "org_name": ctx.org.name}
