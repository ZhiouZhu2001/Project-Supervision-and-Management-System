"""Opaque keyset cursors for the paginated endpoints.

A cursor is the position of the last row already seen, encoded so the client
cannot build one by hand: the sort key is `(business_date, created_at, id)`
descending, which is stable even when several logs share a business day.

Keyset rather than offset because offset re-reads everything before it and
shifts when a row is added; the dataset is small, but a page that skips a log
is a correctness defect, not a performance footnote.
"""

import base64
import binascii
from datetime import date, datetime
from uuid import UUID

_SEPARATOR = "|"


class InvalidCursor(ValueError):
    """The token was not produced by `encode`."""


def encode(day: date, created_at: datetime, row_id: UUID) -> str:
    raw = _SEPARATOR.join((day.isoformat(), created_at.isoformat(), str(row_id)))
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode(token: str) -> tuple[date, datetime, UUID]:
    padded = token + "=" * (-len(token) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        day, created_at, row_id = raw.split(_SEPARATOR)
        return date.fromisoformat(day), datetime.fromisoformat(created_at), UUID(row_id)
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise InvalidCursor("cursor is not valid") from exc
