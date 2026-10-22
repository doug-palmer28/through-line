"""Passwords, usernames, PINs, sign-in tokens, and brute-force protection.

* Passwords and participant PINs: Argon2id (salted, memory-hard) via argon2-cffi.
* Usernames: never stored. We keep an HMAC-SHA256 of the normalized username
  (keyed with the server secret) so we can find the account at login.
* Sign-in: a short-lived signed token (JWT, HS256) in an HttpOnly, SameSite=Strict
  cookie, so page scripts can't read it and other sites can't send it.
  Staff and participants use different cookies, roles, and lifetimes.
* Lockout: after 5 failed sign-ins for the same account within 15 minutes,
  that account is locked for 15 minutes (protects 6-digit PINs).
* The server secret comes from THROUGH_LINE_SECRET, or is generated once into
  data/secret.key (git-ignored). It's never logged or returned.
"""

import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from functools import cache
from pathlib import Path

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from config import PROJECT_DIR

STAFF_COOKIE = "tl_staff"
PARTICIPANT_COOKIE = "tl_participant"
STAFF_TTL = timedelta(hours=8)
PARTICIPANT_TTL = timedelta(hours=2)
MAX_FAILS = 5
LOCK_WINDOW = 15 * 60

_hasher = PasswordHasher()  # Argon2id with library defaults


@cache
def server_secret() -> bytes:
    env = os.getenv("THROUGH_LINE_SECRET")
    if env:
        return env.encode()
    path = Path(os.getenv("THROUGH_LINE_SECRET_FILE", PROJECT_DIR / "data" / "secret.key"))
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    return path.read_text(encoding="utf-8").strip().encode()


def _jwt_key() -> bytes:
    """A 32-byte signing key derived from the server secret (separate from the username-hashing use)."""
    return hashlib.sha256(b"through-line/jwt/" + server_secret()).digest()


# ============================================================ hashing


def hash_secret(plain: str) -> str:
    return _hasher.hash(plain)


def verify_secret(stored_hash: str, plain: str) -> bool:
    try:
        return _hasher.verify(stored_hash, plain)
    except (VerificationError, InvalidHashError):
        return False


# A real hash to verify against when an account doesn't exist, so failed logins take the same time.
_DUMMY_HASH = _hasher.hash("not-a-real-password")


def burn_time(plain: str) -> None:
    verify_secret(_DUMMY_HASH, plain)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def username_hash(username: str) -> str:
    return hmac.new(server_secret(), normalize_username(username).encode(), hashlib.sha256).hexdigest()


def token_hash(token: str) -> str:
    """For invite codes: a keyed hash, so the code itself is never stored."""
    return hmac.new(server_secret(), token.encode(), hashlib.sha256).hexdigest()


# ============================================================ sign-in tokens


def make_token(*, role: str, subject: int, org_id: int, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": str(subject), "org": org_id, "role": role, "iat": now, "exp": now + ttl}
    return jwt.encode(claims, _jwt_key(), algorithm="HS256")


def read_token(token: str | None, role: str) -> dict | None:
    if not token:
        return None
    try:
        claims = jwt.decode(token, _jwt_key(), algorithms=["HS256"], options={"require": ["exp", "sub", "role"]})
    except jwt.PyJWTError:
        return None
    return claims if claims.get("role") == role else None


def cookie_args(ttl: timedelta) -> dict:
    # secure=False only because the prototype runs on http://localhost; set it to True behind HTTPS.
    return {"httponly": True, "samesite": "strict", "secure": os.getenv("THROUGH_LINE_HTTPS") == "1",
            "max_age": int(ttl.total_seconds()), "path": "/"}


# ============================================================ lockout

_fails: dict[str, list[float]] = {}


def _key(kind: str, ident: str) -> str:
    return f"{kind}:{hashlib.sha256(ident.encode()).hexdigest()}"


def locked(kind: str, ident: str) -> bool:
    now = time.time()
    if len(_fails) > 10_000:  # keep memory bounded when someone tries many random usernames
        for k in [k for k, ts in _fails.items() if not ts or now - ts[-1] >= LOCK_WINDOW]:
            del _fails[k]
    recent = [t for t in _fails.get(_key(kind, ident), []) if now - t < LOCK_WINDOW]
    if recent:
        _fails[_key(kind, ident)] = recent
    else:
        _fails.pop(_key(kind, ident), None)
    return len(recent) >= MAX_FAILS


# Per-address limit on sign-in / sign-up attempts (on top of the per-account lockout above), so one
# machine can't hammer passwords, lock out many accounts, or tie the server up with Argon2 work.
IP_WINDOW = 300  # seconds
IP_MAX = 30  # attempts per address per window
_ip_hits: dict[str, list[float]] = {}


def ip_allowed(ip: str) -> bool:
    now = time.time()
    if len(_ip_hits) > 10_000:
        for k in [k for k, ts in _ip_hits.items() if not ts or now - ts[-1] >= IP_WINDOW]:
            del _ip_hits[k]
    hits = [t for t in _ip_hits.get(ip, []) if now - t < IP_WINDOW]
    hits.append(now)
    _ip_hits[ip] = hits
    return len(hits) <= IP_MAX


def record_failure(kind: str, ident: str) -> None:
    _fails.setdefault(_key(kind, ident), []).append(time.time())


def clear_failures(kind: str, ident: str) -> None:
    _fails.pop(_key(kind, ident), None)


# ============================================================ codes


def new_participant_code(prefix: str) -> str:
    return f"{prefix}-{secrets.randbelow(9000) + 1000}{secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"


def new_pin() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_invite_code() -> str:
    return secrets.token_urlsafe(9)


# ============================================================ the shared demo account

# A ready-made example whose password is published for graders: it can look at everything and download
# anything, but can't change anything, and wrong passwords never lock it.
DEMO_USERNAME = os.getenv("THROUGH_LINE_DEMO_USERNAME", "keystone.demo")
DEMO_READ_ONLY = "This shared demo is view-only. Create your own account with the access code to try the AI tools."


def is_demo(username_hash_value: str) -> bool:
    return bool(DEMO_USERNAME) and hmac.compare_digest(username_hash_value, username_hash(DEMO_USERNAME))


# ============================================================ uploads

MAX_UNZIPPED_BYTES = 100 * 1024 * 1024
MAX_ZIP_ENTRIES = 2000


def check_zip(data: bytes) -> None:
    """Word, PowerPoint, and Excel files are zip packages. Refuse ones that would expand to something huge
    (a "zip bomb") before any library unpacks them. Raises ValueError."""
    import io
    import zipfile

    try:
        info = zipfile.ZipFile(io.BytesIO(data)).infolist()
    except zipfile.BadZipFile as exc:
        raise ValueError("That file is damaged or isn't a real Office file.") from exc
    if len(info) > MAX_ZIP_ENTRIES or sum(i.file_size for i in info) > MAX_UNZIPPED_BYTES:
        raise ValueError("That file is too large once opened.")
