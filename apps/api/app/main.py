import logging
from contextlib import asynccontextmanager
from typing import Annotated, Any
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap import ensure_account, run_migrations
from app.clock import now_utc
from app.config import DEVELOPMENT_PASSWORD, DEVELOPMENT_SECRET, get_settings
from app.db import check_database, dispose_engine, get_session, get_session_factory
from app.errors import ApiError, api_error_handler, error_body
from app.jobs.scheduler import JOB_ID, build_scheduler, catch_up
from app.routers.attachments import router as attachments_router
from app.routers.auth import router as auth_router
from app.routers.calendar import router as calendar_router
from app.routers.export import router as export_router
from app.routers.logs import router as logs_router
from app.routers.projects import router as projects_router
from app.routers.settings import router as settings_router
from app.routers.stats import router as stats_router
from app.routers.today import router as today_router
from app.services.alerts import last_judged_business_date
from app.services.mail import build_mailer

# uvicorn already configures this logger, so the scheduling line appears in
# the same stream as the server's own startup messages.
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    if settings.run_migrations:
        await run_migrations()
        async with get_session_factory()() as session:
            await ensure_account(session, email=settings.app_email, password=settings.app_password)
            await session.commit()

    scheduler = None
    if settings.scheduler_enabled:
        mailer = build_mailer()
        target = settings.alert_email or settings.app_email
        # A restart across 21:00 must not lose the day: judge it on the way up.
        await catch_up(
            session_factory=get_session_factory(),
            mailer=mailer,
            to=target,
            base_url=settings.app_base_url,
        )
        scheduler = build_scheduler(
            session_factory=get_session_factory(),
            mailer=mailer,
            to=target,
            base_url=settings.app_base_url,
        )
        scheduler.start()
        job = scheduler.get_job(JOB_ID)
        logger.info(
            "alert digest scheduled; next run at %s",
            job.next_run_time.isoformat() if job and job.next_run_time else "unknown",
        )

    yield

    if scheduler is not None:
        scheduler.shutdown(wait=False)
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    # The development secret and password are committed on purpose so that
    # `make dev` works on a clean clone. Running with them in production would
    # make every session cookie forgeable and the login publicly known, so the
    # process refuses to start instead.
    if settings.app_env == "production":
        if settings.app_secret_key == DEVELOPMENT_SECRET:
            raise RuntimeError("APP_SECRET_KEY must be set when APP_ENV=production")
        if settings.app_password == DEVELOPMENT_PASSWORD:
            raise RuntimeError("APP_PASSWORD must be set when APP_ENV=production")

    app = FastAPI(
        title="Project Supervision and Management System",
        version=settings.app_version,
        # No interactive docs on a single-user diary application: the schema
        # is not public information and the surface is one client.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    app.add_exception_handler(ApiError, api_error_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # The framework's default body is a list of internal locations; the
        # client contract is the single error shape, so translate it once here.
        # `ctx` can carry a raw exception object (a field validator's
        # ValueError), which is not JSON serialisable, so it is stringified.
        errors = []
        for error in exc.errors():
            cleaned = {key: value for key, value in error.items() if key != "ctx"}
            context = error.get("ctx")
            if context:
                cleaned["ctx"] = {key: str(value) for key, value in context.items()}
            errors.append(cleaned)

        return JSONResponse(
            error_body("VALIDATION_ERROR", "Request validation failed", {"errors": errors}),
            status_code=422,
        )

    @app.middleware("http")
    async def reject_foreign_origins(request: Request, call_next: Any):
        """CSRF defence for cookie-authenticated writes (see architecture §7).

        The comparison is against the request's own Host, not a configured
        base URL: `localhost:8080` and `127.0.0.1:8080` are the same origin as
        far as the browser is concerned, and a configured value would reject
        one of them. A request with no Origin header is a non-browser client
        and is allowed — it carries no ambient cookie.
        """
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if origin is not None:
                origin_host = urlsplit(origin).hostname
                host_header = request.headers.get("host", "")
                host = host_header.rsplit(":", 1)[0] if host_header.count(":") == 1 else host_header
                allowed = {host, urlsplit(settings.app_base_url).hostname}
                if origin_host not in allowed:
                    return JSONResponse(
                        error_body("ORIGIN_REJECTED", "Cross-origin request rejected"),
                        status_code=403,
                    )
        return await call_next(request)

    app.include_router(auth_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(logs_router, prefix="/api")
    app.include_router(calendar_router, prefix="/api")
    app.include_router(attachments_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(stats_router, prefix="/api")
    app.include_router(export_router, prefix="/api")
    app.include_router(today_router, prefix="/api")

    @app.get("/api/healthz", tags=["ops"])
    async def healthz(db: Annotated[AsyncSession, Depends(get_session)]) -> JSONResponse:
        """Unauthenticated liveness plus a real database round trip.

        Returns 503 when the database is unreachable: a health check that
        reports success while the database is down is worse than none. The
        last judged business day is part of the answer, because a scheduler
        that stopped is a defect nobody would otherwise notice.
        """
        database_ok = await check_database()
        last_alert = None
        if database_ok:
            try:
                # Read through the request's session, so the check exercises
                # the path the rest of the app uses.
                await db.execute(text("SELECT 1"))
                last = await last_judged_business_date(db)
                last_alert = last.isoformat() if last is not None else None
            except Exception:
                last_alert = None

        body: dict[str, Any] = {
            "status": "ok" if database_ok else "degraded",
            "db": database_ok,
            "version": settings.app_version,
            "env": settings.app_env,
            "time": now_utc().isoformat(),
            "last_alert_business_date": last_alert,
        }
        return JSONResponse(body, status_code=200 if database_ok else 503)

    return app


app = create_app()
