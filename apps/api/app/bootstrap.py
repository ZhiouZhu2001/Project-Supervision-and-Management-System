"""Startup work: schema migrations and seeding the single account.

Both are idempotent, because they run on every boot in development where the
server reloads on every edit. Nothing here is allowed to destroy data.
"""

import asyncio
from pathlib import Path

from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alembic import command
from app.config import get_settings
from app.db import get_session_factory
from app.models.account import Account
from app.security import hash_password


def _alembic_config() -> Config:
    root = Path(__file__).resolve().parent.parent
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    return config


def _upgrade() -> None:
    command.upgrade(_alembic_config(), "head")


async def run_migrations() -> None:
    # Alembic's environment is synchronous; running it in a worker thread
    # keeps the event loop free and avoids nesting asyncio.run inside it.
    await asyncio.to_thread(_upgrade)


async def ensure_account(session: AsyncSession, *, email: str, password: str) -> bool:
    """Create the account if it does not exist. Returns True if created.

    Never overwrites an existing password: silently resetting credentials
    because an environment variable changed would be a backdoor.
    """
    existing = await session.scalar(select(Account).where(Account.email == email.lower()))
    if existing is not None:
        return False

    session.add(
        Account(
            email=email.lower(),
            password_hash=hash_password(password),
            display_name="Owner",
        )
    )
    await session.flush()
    return True


async def seed_from_settings() -> None:
    settings = get_settings()
    async with get_session_factory()() as session:
        await ensure_account(session, email=settings.app_email, password=settings.app_password)
        await session.commit()
