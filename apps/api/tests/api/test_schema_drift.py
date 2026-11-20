"""The migrations and the models must describe the same database.

This exists because of a real defect: revision 0012 renamed a column but left
its check constraint behind, and the suite stayed green because the test
database is built from `Base.metadata` — the constraint only existed in the
migration. The application then refused to start.

So one test applies the *migrations* to an empty database and asks Alembic to
compare that schema with the models. Any difference is a boot-time bug waiting
to happen.
"""

import os
import subprocess
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.models import Base
from tests.conftest import _create_database_if_missing, _test_database_url

SCRATCH = "supervision_migtest"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
async def migrated_database_url() -> str:
    url = make_url(_test_database_url()).set(database=SCRATCH)
    url_str = url.render_as_string(hide_password=False)
    await _create_database_if_missing(url_str)

    engine = create_async_engine(url)
    try:
        # A previous run must not leave its schema behind.
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))

        # In a subprocess because alembic/env.py takes its URL from the
        # application settings, which this process has already cached.
        completed = subprocess.run(
            ["uv", "run", "--no-sync", "alembic", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            env={**os.environ, "DATABASE_URL": url_str},
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
    finally:
        await engine.dispose()

    return url_str


async def test_the_models_describe_the_schema_the_migrations_create(
    migrated_database_url: str,
) -> None:
    engine = create_async_engine(migrated_database_url)
    try:
        async with engine.connect() as connection:

            def compare(sync_connection) -> list:
                context = MigrationContext.configure(sync_connection)
                return compare_metadata(context, Base.metadata)

            differences = await connection.run_sync(compare)
    finally:
        await engine.dispose()

    assert differences == [], (
        "the migrations and the models disagree:\n"
        + "\n".join(f"  {difference}" for difference in differences)
    )
