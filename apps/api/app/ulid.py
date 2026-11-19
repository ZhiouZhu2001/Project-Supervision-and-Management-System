"""ULID: a sortable, random identifier for stored files (ARCH 8).

A ULID is a 48-bit millisecond timestamp followed by 80 random bits, encoded
as 26 Crockford base32 characters. It is used instead of a bare uuid4 because
the timestamp prefix makes a directory listing sort roughly by upload time,
and because AGENTS requires an identifier rather than the user's filename.
"""

import secrets
from datetime import datetime

from app.clock import now_utc

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_TIMESTAMP_BITS = 48
_RANDOM_BITS = 80
LENGTH = 26


def new_ulid(instant: datetime | None = None) -> str:
    """26 characters: millisecond timestamp first, 80 random bits after."""
    millis = int((instant or now_utc()).timestamp() * 1000) & ((1 << _TIMESTAMP_BITS) - 1)
    value = (millis << _RANDOM_BITS) | secrets.randbits(_RANDOM_BITS)

    characters: list[str] = []
    for _ in range(LENGTH):
        characters.append(_ALPHABET[value & 0b11111])
        value >>= 5
    return "".join(reversed(characters))
