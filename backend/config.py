"""Shared settings for the Through Line backend.

Every agent reads its model from here so the model can't drift between agents.
Secrets come from the environment / .env only and are never logged or returned by the API.
"""

import os
from pathlib import Path

from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent


def _load_env() -> None:
    """Read .env from this repo's folder first, then from the folder above it (where a shared .env with
    PORTKEY_API_KEY may live). Anything already set in the environment wins, including a deliberately empty
    value (that's how the offline tests keep the key out). Blank lines in a .env, such as an untouched copy of
    .env.example, never hide a real value further up."""
    preset = set(os.environ)
    for path in (PROJECT_DIR / ".env", PROJECT_DIR.parent / ".env"):
        for key, value in dotenv_values(path).items():
            if key not in preset and value and not os.environ.get(key):
                os.environ[key] = value


_load_env()

APP_NAME = "Through Line"
MODEL_NAME = "gpt-6-luna"  # Project rule: every agent uses Luna. Not configurable per agent.

FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

OUTPUT_DIR = PROJECT_DIR / "output"
AUDIT_LOG_PATH = OUTPUT_DIR / "audit_log.json"


def signup_code() -> str | None:
    """If set (on the live site), starting a new organization requires this code; colleagues join with invites."""
    return os.getenv("THROUGH_LINE_SIGNUP_CODE") or None


def portkey_key_present() -> bool:
    """True if the key is available. Never returns or prints the key itself."""
    return bool(os.getenv("PORTKEY_API_KEY"))
