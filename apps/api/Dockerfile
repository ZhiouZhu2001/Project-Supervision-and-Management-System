# The uv binary is copied from its official image rather than installed with
# pip, so the same resolver version produces the same lock in CI, on the
# developer machine and on the server.
FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    TZ=UTC
WORKDIR /app

# Dependencies are resolved from the lock file only. A lock that does not
# match pyproject.toml fails the build instead of silently drifting.
FROM base AS dev
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

FROM base AS runtime
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# One worker: the scheduler runs in-process and must not be duplicated.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
