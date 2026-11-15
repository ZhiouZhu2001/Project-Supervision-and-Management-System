"""Login attempt throttling.

In memory, on purpose. The architecture commits to a single process (the
scheduler relies on it), so a distributed counter would be machinery guarding
against a scenario that cannot occur. A restart clears the counters, which
costs an attacker a few seconds and costs this system nothing — the real
defence is the password, and this only removes the free-retry loop.

Keyed on (email, source address). Keying on the account alone would let one
host lock the owner out indefinitely; keying on the address alone would let an
attacker with many addresses ignore the limit entirely.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.clock import now_utc

MAX_FAILURES = 5
LOCK_FOR = timedelta(minutes=15)
_PRUNE_ABOVE = 1_000


@dataclass
class _Entry:
    failures: int = 0
    locked_until: datetime | None = None


def normalize_email(email: str) -> str:
    """Case and surrounding whitespace must not create a second identity."""
    return email.strip().lower()


class LoginThrottle:
    def __init__(self, max_failures: int = MAX_FAILURES, lock_for: timedelta = LOCK_FOR) -> None:
        self._max_failures = max_failures
        self._lock_for = lock_for
        self._entries: dict[tuple[str, str], _Entry] = {}

    @staticmethod
    def _key(email: str, source: str) -> tuple[str, str]:
        return (normalize_email(email), source or "")

    def is_locked(self, email: str, source: str) -> bool:
        entry = self._entries.get(self._key(email, source))
        if entry is None or entry.locked_until is None:
            return False
        if entry.locked_until <= now_utc():
            # Lock served; the slate starts clean rather than at the limit.
            entry.failures = 0
            entry.locked_until = None
            return False
        return True

    def note_failure(self, email: str, source: str) -> None:
        key = self._key(email, source)
        entry = self._entries.setdefault(key, _Entry())
        entry.failures += 1
        if entry.failures >= self._max_failures:
            entry.locked_until = now_utc() + self._lock_for
        self._prune()

    def note_success(self, email: str, source: str) -> None:
        self._entries.pop(self._key(email, source), None)

    def reset(self) -> None:
        """Test hook. Production never calls this."""
        self._entries.clear()

    def _prune(self) -> None:
        """Keep the dict from growing without bound on a long-lived process."""
        if len(self._entries) <= _PRUNE_ABOVE:
            return
        now = now_utc()
        stale = [
            key
            for key, entry in self._entries.items()
            if entry.locked_until is None or entry.locked_until <= now
        ]
        for key in stale:
            self._entries.pop(key, None)


login_throttle = LoginThrottle()
