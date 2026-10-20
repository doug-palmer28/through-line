"""Through Line API (and, in production, the website itself).

Local development, from the backend folder (Vite serves the frontend on :5173):
    uvicorn main:app --reload --reload-dir . --port 8000

Production (Dockerfile / Render): the built frontend in frontend/dist is served from the
same origin as the API, so the SameSite=Strict sign-in cookies just work.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.formparsers import MultiPartParser

import security
from config import APP_NAME, FRONTEND_ORIGINS, PROJECT_DIR
from routes import auth, dashboard, grants, logic_model, participant, reports, system, tools, usage

# Largest request we accept: 5 files × 10 MB plus form fields. Checked before the body is read.
MAX_REQUEST_BYTES = 52 * 1024 * 1024
# Privacy: keep uploads in memory. Starlette spills file parts over 1 MB to a temp file on
# disk; raising the spool limit to the request cap means an accepted upload never touches disk.
MultiPartParser.spool_max_size = MAX_REQUEST_BYTES
SIGN_IN_PATHS = {"/api/auth/login", "/api/auth/signup", "/api/auth/participant/login"}

production = os.getenv("THROUGH_LINE_HTTPS") == "1"
app = FastAPI(title=f"{APP_NAME} API", version="0.1.0",
              docs_url=None if production else "/docs", redoc_url=None,
              openapi_url=None if production else "/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    """422 without echoing the submitted values back (they may be private, or not even valid JSON, like NaN)."""
    return JSONResponse({"detail": [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")}
                                    for e in exc.errors()]}, status_code=422)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        size = request.headers.get("content-length")
        if size is None and "multipart/form-data" in request.headers.get("content-type", ""):
            return JSONResponse({"detail": "Uploads need a Content-Length header."}, status_code=411)
        if size is not None and (not size.isdigit() or int(size) > MAX_REQUEST_BYTES):
            return JSONResponse({"detail": "That upload is too large."}, status_code=413)
        if request.url.path in SIGN_IN_PATHS and not security.ip_allowed(request.client.host if request.client else "?"):
            return JSONResponse({"detail": "Too many attempts from this network. Please wait a few minutes."},
                                status_code=429)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")  # private data: never cache API responses
    return response


app.include_router(system.router)
app.include_router(auth.router)
app.include_router(participant.router)
app.include_router(logic_model.router)
app.include_router(tools.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(grants.router)
app.include_router(usage.router)


def mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the built React app: real files as-is, every other non-API path gets index.html (client routing)."""
    root = dist.resolve()
    if (root / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not found.")
        file = (root / path).resolve()
        if path and file.is_file() and root in file.parents:
            return FileResponse(file)
        return FileResponse(root / "index.html")


DIST = Path(os.getenv("THROUGH_LINE_FRONTEND_DIST") or PROJECT_DIR / "frontend" / "dist")
if (DIST / "index.html").is_file():
    mount_frontend(app, DIST)
