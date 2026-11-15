import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.bootstrap import ensure_account
from app.config import get_settings
from app.db import get_session
from app.main import create_app
from app.models import Base

ACCOUNT_EMAIL = "owner@example.com"
ACCOUNT_PASSWORD = "correct horse battery staple"


def _test_database_url() -> str:
    """Never point tests at the development database.

    A dedicated `<name>_test` database is created on first run, so a mistaken
    truncate can only destroy test data.
    """
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit
    url = make_url(get_settings().database_url)
    if not url.database:
        raise RuntimeError("DATABASE_URL has no database name")
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


async def _create_database_if_missing(url_str: str) -> None:
    url = make_url(url_str)
    admin = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        async with admin.connect() as connection:
            exists = await connection.scalar(
                text("select 1 from pg_database where datname = :name"), {"name": url.database}
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        await admin.dispose()


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    url = _test_database_url()
    await _create_database_if_missing(url)
    eng = create_async_engine(url)
    try:
        async with eng.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        yield eng
    finally:
        await eng.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def account(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as session:
        await ensure_account(session, email=ACCOUNT_EMAIL, password=ACCOUNT_PASSWORD)
        await session.commit()


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession], account: None
) -> AsyncIterator[AsyncClient]:
    app = create_app()

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
    app.dependency_overrides.clear()
