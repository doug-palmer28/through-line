"""Health check: lets the frontend confirm it can reach the backend."""

from fastapi import APIRouter

from config import APP_NAME, MODEL_NAME, portkey_key_present, signup_code

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "model": MODEL_NAME,
        "llm_key_configured": portkey_key_present(),
        "signup_code_required": signup_code() is not None,
    }
