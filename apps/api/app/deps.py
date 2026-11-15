"""Request-scoped authentication dependencies."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.db import get_session
from app.errors import unauthenticated
from app.models.account import Account
from app.models.session import Session
from app.security import hash_token

COOKIE_NAME = "sid"


async def get_current_account(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Account:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise unauthenticated()

    row = await db.scalar(select(Session).where(Session.token_hash == hash_token(token)))
    if row is None:
        # No row means logged out or revoked, which is not the same as expired.
        raise unauthenticated()
    if row.expires_at <= now_utc():
        raise unauthenticated("Session expired")

    account = await db.get(Account, row.account_id)
    if account is None:
        raise unauthenticated()

    # last_seen is written at most once a day: a write on every request would
    # turn a read path into a write path for no benefit.
    now = now_utc()
    if (now - row.last_seen_at).total_seconds() > 86_400:
        row.last_seen_at = now

    return account


CurrentAccount = Annotated[Account, Depends(get_current_account)]
