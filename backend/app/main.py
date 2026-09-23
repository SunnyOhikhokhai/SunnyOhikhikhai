from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_, select
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import get_settings
from .database import SessionLocal
from .errors import ApiError
from .routers import admin, auth, community, content, notifications, public, users

log = logging.getLogger("nipam")
settings = get_settings()


def run_scheduled_jobs() -> None:
    """Dispatch notifications for scheduled announcements whose time has come."""
    from .models import Announcement, utcnow
    from .routers.admin import dispatch_announcement

    with SessionLocal() as db:
        due = db.scalars(
            select(Announcement).where(
                Announcement.status == "published",
                Announcement.notified_at.is_(None),
                Announcement.publish_at.is_not(None),
                Announcement.publish_at <= utcnow(),
                or_(Announcement.expires_at.is_(None), Announcement.expires_at > utcnow()),
            )
        ).all()
        for a in due:
            dispatch_announcement(db, a)


async def _scheduler() -> None:
    while True:
        try:
            await asyncio.to_thread(run_scheduled_jobs)
        except Exception:  # pragma: no cover - keep the loop alive
            log.exception("scheduled job failed")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_scheduler()) if settings.env != "test" else None
    yield
    if task:
        task.cancel()


app = FastAPI(
    title="NIPAM API",
    version="1.0.0",
    description="Non-Indigenes for Philip Aduda Movement — community platform API.",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/api/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    h = response.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("X-Frame-Options", "DENY")
    h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/"):
        h.setdefault("Cache-Control", "no-store")
        h.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    if settings.is_production:
        h.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
    return response


def _error(status: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(body, status_code=status)


@app.exception_handler(ApiError)
async def api_error_handler(_: Request, exc: ApiError):
    return _error(exc.status, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    fields = {}
    for e in exc.errors():
        loc = [str(p) for p in e.get("loc", []) if p not in ("body", "query", "path")]
        msg = e.get("msg", "Invalid value").removeprefix("Value error, ")
        fields[".".join(loc) or "request"] = msg
    first = next(iter(fields.values()), "Invalid request")
    return _error(422, "validation_error", first, {"fields": fields})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    return _error(exc.status_code, code, str(exc.detail))


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):  # pragma: no cover
    log.exception("unhandled error", exc_info=exc)
    return _error(500, "server_error", "Something went wrong on our side. Please try again.")


for r in (auth.router, users.router, users.members, content.router, community.router, notifications.router, public.router, admin.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"data": {"status": "ok"}}


# Uploaded files (local storage backend). In production serve these from the
# object store/CDN instead.
_uploads = Path(settings.upload_dir)
_uploads.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads), name="uploads")

# Optionally serve the built SPA (single-container deployment).
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():  # pragma: no cover - depends on build
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            return _error(404, "not_found", "Not found")
        f = _dist / path
        if path and f.is_file() and _dist in f.resolve().parents:
            return FileResponse(f)
        return FileResponse(_dist / "index.html")
