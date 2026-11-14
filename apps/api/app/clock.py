"""The only place in the application that is allowed to read the wall clock.

Invariant 7: `datetime.now()` is banned everywhere else. Service functions
take an instant as an argument so that tests can state what "now" is instead
of freezing the system clock.
"""

from datetime import UTC, datetime


def now_utc() -> datetime:
    return datetime.now(tz=UTC)
