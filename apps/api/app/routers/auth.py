from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.config import get_settings
from app.db import get_session
from app.deps import COOKIE_NAME, CurrentAccount
from app.errors import invalid_credentials, unauthenticated
from app.models.account import Account
from app.models.session import Session
from app.net import client_ip
from app.security import (
    SESSION_TTL,
    build_session,
    hash_token,
    new_session_token,
    verify_password,
)
from app.throttle import login_throttle

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class AccountView(BaseModel):
    email: str
    display_name: str | None
    timezone: str


def _view(account: Account) -> AccountView:
    return AccountView(
        email=account.email,
        display_name=account.display_name,
        timezone=account.timezone,
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AccountView:
    settings = get_settings()
    source = client_ip(request)

    # A locked account answers exactly like a wrong password. Confirming the
    # lock would confirm that the account exists, and the wait is short enough
    # that hiding it costs the owner nothing.
    if login_throttle.is_locked(payload.email, source):
        raise invalid_credentials()

    account = await db.scalar(select(Account).where(Account.email == payload.email.lower()))

    # verify_password is called even when the account is missing, so the
    # response time does not reveal whether an email exists.
    if not verify_password(payload.password, account.password_hash if account else None):
        login_throttle.note_failure(payload.email, source)
        raise invalid_credentials()
    assert account is not None

    login_throttle.note_success(payload.email, source)

    token = new_session_token()
    session = build_session(
        account.id,
        token,
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(session)
    await db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return _view(account)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        await db.execute(delete(Session).where(Session.token_hash == hash_token(token)))
        await db.commit()

    response.delete_cookie(COOKIE_NAME, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    await db.execute(delete(Session).where(Session.account_id == account.id))
    await db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me")
async def me(account: CurrentAccount) -> AccountView:
    _ = now_utc()  # keeps the clock dependency explicit for future use
    return _view(account)


__all__ = ["router", "unauthenticated"]
