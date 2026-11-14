from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.clock import now_utc
from app.config import get_settings
from app.db import check_database, dispose_engine

DEVELOPMENT_SECRET = "dev-only-not-a-secret"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    # The development secret is committed on purpose so that `make dev` works
    # on a clean clone. Running with it in production would make every session
    # cookie forgeable, so the process refuses to start instead.
    if settings.app_env == "production" and settings.app_secret_key == DEVELOPMENT_SECRET:
        raise RuntimeError("APP_SECRET_KEY must be set when APP_ENV=production")

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

    @app.get("/api/healthz", tags=["ops"])
    async def healthz() -> JSONResponse:
        """Unauthenticated liveness plus a real database round trip.

        Returns 503 when the database is unreachable: a health check that
        reports success while the database is down is worse than none.
        """
        database_ok = await check_database()
        body: dict[str, Any] = {
            "status": "ok" if database_ok else "degraded",
            "db": database_ok,
            "version": settings.app_version,
            "env": settings.app_env,
            "time": now_utc().isoformat(),
        }
        return JSONResponse(body, status_code=200 if database_ok else 503)

    return app


app = create_app()
