"""Shared settings for the Through Line backend.

Every agent reads its model from here so the model can't drift between agents.
Secrets come from the environment / .env only and are never logged or returned by the API.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

# Project .env first, then the course-root .env one level up (holds PORTKEY_API_KEY).
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")

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
