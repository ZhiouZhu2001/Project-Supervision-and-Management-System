"""The only streak implementation (invariant 3).

A streak counts backwards from the most recent expected day through days that
were recorded, stopping at the first expected day that was not. Everything
that needs a streak calls this module: no SQL, no client, no script is allowed
to recompute it, because two implementations that disagree produce two truths.

Two rules are easy to get wrong and are therefore stated here:

* **Today does not break the chain while it is still running.** An unrecorded
  today is skipped, not counted as a miss.
* **A day that is not an expected day is invisible.** Rest days and paused
  periods are neither counted nor breaking; they simply are not in the list.
"""

from collections.abc import Callable, Sequence
from datetime import date, timedelta

WINDOW_DAYS = 400

# R11: the flame appears at exactly this many consecutive days.
FLAME_THRESHOLD = 7


def window_start(today: date) -> date:
    """Oldest day included in a bounded reporting window.

    This is a *reporting* bound (the twelve-week statistics rollup), never a
    streak bound: R6's longest streak has to see the project's whole life, or
    the record it is supposed to keep forever would quietly shrink.
    """
    return today - timedelta(days=WINDOW_DAYS)


def expected_days(
    start: date,
    end: date,
    *,
    rest_weekdays: frozenset[int] = frozenset(),
    rest_for: Callable[[date], frozenset[int]] | None = None,
) -> list[date]:
    """Days the owner was expected to record in `[start, end]`, ascending.

    `rest_weekdays` is a constant set; `rest_for` resolves the set per day and
    wins when supplied, because a rule change must not rewrite history (R14).
    """
    if end < start:
        return []

    days: list[date] = []
    cursor = start
    while cursor <= end:
        rest = rest_for(cursor) if rest_for is not None else rest_weekdays
        if cursor.isoweekday() not in rest:
            days.append(cursor)
        cursor += timedelta(days=1)
    return days


def current_streak(days: Sequence[date], checked: set[date], today: date) -> int:
    """Count consecutive recorded expected days, backwards from `today`.

    `days` must be ascending expected days that already exclude rest days and
    paused periods; `checked` is the set of business days with at least one
    log.
    """
    if not days:
        return 0

    index = len(days) - 1
    if days[index] == today and today not in checked:
        # The day is not over, so today cannot be a miss yet.
        index -= 1

    total = 0
    while index >= 0 and days[index] in checked:
        total += 1
        index -= 1
    return total


def consecutive_misses(days: Sequence[date], checked: set[date]) -> int:
    """How many expected days in a row are unrecorded, counting back (R12).

    Lives here rather than in the digest so the number in the email and the
    number in the app cannot disagree (invariant 3). Only expected days count:
    a rest day or a paused stretch is absent from `days`, so a gap in the
    calendar is not a gap in the record.
    """
    run = 0
    for day in reversed(days):
        if day in checked:
            break
        run += 1
    return run


def longest_streak(days: Sequence[date], checked: set[date]) -> int:
    """Best ever run, for the record that must never shrink (R6)."""
    best = 0
    run = 0
    for day in days:
        if day in checked:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best
