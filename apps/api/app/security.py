"""Password hashing and session tokens.

Two rules are enforced here rather than at the call sites:

* passwords are verified against a memory-hard hash, never compared as text;
* only the SHA-256 of a session token is ever written to the database, so a
  database dump does not contain usable credentials.
"""

import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.clock import now_utc
from app.models.session import Session

SESSION_TTL = timedelta(days=30)
_hasher = PasswordHasher()

# A dummy hash used to keep the timing of "unknown account" indistinguishable
# from "wrong password" once login exists for a single account.
_DUMMY_HASH = _hasher.hash("timing-equalizer")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        _hasher.verify(password_hash or _DUMMY_HASH, password)
        return password_hash is not None
    except (VerifyMismatchError, VerificationError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_session(
    account_id: UUID, token: str, *, user_agent: str | None, ip: str | None
) -> Session:
    now = now_utc()
    return Session(
        account_id=account_id,
        token_hash=hash_token(token),
        expires_at=now + SESSION_TTL,
        last_seen_at=now,
        user_agent=(user_agent or "")[:255] or None,
        ip=ip,
    )
