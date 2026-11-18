"""Rest-day rules (R7) and their effective-date semantics (R14).

A rule is `(effective_from, weekdays)`. The rule in force on a day is the
latest one whose effective date has arrived, which is what makes a change
today leave yesterday's streak alone: history is never rewritten, it is
resolved day by day against the rules that existed then.
"""

from collections.abc import Sequence
from datetime import date

DEFAULT_REST_WEEKDAYS: frozenset[int] = frozenset({6, 7})

RestRule = tuple[date, frozenset[int]]


def rest_weekdays_for(
    day: date,
    rules: Sequence[RestRule],
    default: frozenset[int] = DEFAULT_REST_WEEKDAYS,
) -> frozenset[int]:
    """Weekdays that count as rest on `day`.

    `rules` must be ascending by effective date. A rule that starts later than
    `day` is not consulted — that is the whole point of the effective date.
    """
    chosen = default
    for effective_from, weekdays in rules:
        if effective_from > day:
            break
        chosen = weekdays
    return chosen


def resolver(
    rules: Sequence[RestRule],
    default: frozenset[int] = DEFAULT_REST_WEEKDAYS,
):
    """Turn a rule list into the per-day callable the streak kernel expects."""

    def rest_on(day: date) -> frozenset[int]:
        return rest_weekdays_for(day, rules, default)

    return rest_on


def validate_rest_weekdays(weekdays: Sequence[int]) -> frozenset[int]:
    """Reject values that would stop the product working.

    An empty set is allowed — it means "no rest days". All seven is refused,
    because it means no expected days, which means every streak is
    permanently zero: an easy mistake to make and a confusing one to debug.
    """
    unique = sorted({int(weekday) for weekday in weekdays})
    if unique and (unique[0] < 1 or unique[-1] > 7):
        raise ValueError("weekdays are ISO numbers between 1 and 7")
    if set(unique) == set(range(1, 8)):
        raise ValueError("at least one weekday must stay expected")
    return frozenset(unique)
