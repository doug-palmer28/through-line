import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

# Offline only: these tests must never reach the real model. An empty value (not a missing one)
# also stops config.py's load_dotenv from pulling the real key back in from a .env file.
os.environ["PORTKEY_API_KEY"] = ""
os.environ["THROUGH_LINE_SECRET"] = "test-secret-not-for-production-use-only-0123456789"
os.environ.pop("THROUGH_LINE_SIGNUP_CODE", None)
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Every TestClient comes from the same address; start each test with a clean slate."""
    import security

    security._ip_hits.clear()
    security._fails.clear()
    yield


@pytest.fixture
def org_env(tmp_path, monkeypatch):
    """A signed-in organization with an approved plan and survey tools, on throwaway data, offline."""
    monkeypatch.setenv("THROUGH_LINE_AUDIT", str(tmp_path / "audit_log.json"))
    monkeypatch.setenv("THROUGH_LINE_SESSIONS", str(tmp_path / "sessions"))
    monkeypatch.setenv("THROUGH_LINE_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("THROUGH_LINE_BRAND_DIR", str(tmp_path / "brand"))
    from fastapi.testclient import TestClient
    from pydantic_ai.models.test import TestModel

    sys.path.insert(0, str(Path(__file__).parent))
    from test_prototype import STAFF, _with_plan

    from agents import common
    import main

    monkeypatch.setattr(common, "MODEL_OVERRIDE", TestModel())
    c = TestClient(main.app)
    assert c.post("/api/auth/signup", json=STAFF).status_code == 200
    _with_plan(main.app, c)
    c.post("/api/tools/build")
    return c, tmp_path
