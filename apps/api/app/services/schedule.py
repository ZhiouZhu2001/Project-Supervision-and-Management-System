"""Rest-day rules (R7) and their effective-date semantics (R14).

A rule is `(effective_from, weekdays)`. The rule in force on a day is the
latest one whose effective date has arrived, which is what makes a change
today leave yesterday's streak alone: history is never rewritten, it is
resolved day by day against the rules that existed then.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import ScheduleRule

DEFAULT_REST_WEEKDAYS: frozenset[int] = frozenset({6, 7})

RestRule = tuple[date, frozenset[int] | None]
# A None weekday set is an appended row that closes an override: from its
# effective date the project follows the account default in force that day.
# Deleting the old rows instead would rewrite what past days meant (R14).


async def load_rules(
    db: AsyncSession, *, until: date
) -> tuple[list[RestRule], dict[UUID, list[RestRule]]]:
    """Rules in force up to `until`, split into the account default and overrides."""
    rows = list(
        await db.scalars(
            select(ScheduleRule)
            .where(ScheduleRule.effective_from <= until)
            .order_by(ScheduleRule.effective_from)
        )
    )

    global_rules: list[RestRule] = []
    by_project: dict[UUID, list[RestRule]] = {}
    for rule in rows:
        entry: RestRule = (
            rule.effective_from,
            None if rule.inherits_default else frozenset(rule.rest_weekdays),
        )
        if rule.project_id is None:
            global_rules.append(entry)
        else:
            by_project.setdefault(rule.project_id, []).append(entry)
    return global_rules, by_project


def rest_weekdays_for(
    day: date,
    rules: Sequence[RestRule],
    default: frozenset[int] = DEFAULT_REST_WEEKDAYS,
) -> frozenset[int]:
    """Weekdays that count as rest on `day`.

    `rules` must be ascending by effective date. A rule that starts later than
    `day` is not consulted â€” that is the whole point of the effective date.
    """
    chosen: frozenset[int] | None = None
    for effective_from, weekdays in rules:
        if effective_from > day:
            break
        chosen = weekdays
    return default if chosen is None else chosen


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

    An empty set is allowed â€” it means "no rest days". All seven is refused,
    because it means no expected days, which means every streak is
    permanently zero: an easy mistake to make and a confusing one to debug.
    """
    unique = sorted({int(weekday) for weekday in weekdays})
    if unique and (unique[0] < 1 or unique[-1] > 7):
        raise ValueError("weekdays are ISO numbers between 1 and 7")
    if set(unique) == set(range(1, 8)):
        raise ValueError("at least one weekday must stay expected")
    return frozenset(unique)



@dataclass
class ScheduleInForce:
    """Which rest days apply to a project today, and where they come from.

    `inherited` is what the screen shows the owner: an override in force, or
    the account default. The resolved weekdays are the same either way.
    """

    rest_weekdays: frozenset[int]
    effective_from: date | None
    inherited: bool


async def latest_rule(
    db: AsyncSession, *, project_id: UUID | None, until: date
) -> ScheduleRule | None:
    """Newest row for this project (or the account, when `project_id` is None)."""
    condition = (
        ScheduleRule.project_id.is_(None)
        if project_id is None
        else ScheduleRule.project_id == project_id
    )
    return await db.scalar(
        select(ScheduleRule)
        .where(condition, ScheduleRule.effective_from <= until)
        .order_by(ScheduleRule.effective_from.desc())
        .limit(1)
    )


async def schedule_in_force(
    db: AsyncSession, *, project_id: UUID, today: date
) -> ScheduleInForce:
    """R7/R14: the override in force, or the account default it inherits."""
    own = await latest_rule(db, project_id=project_id, until=today)
    # The latest own row decides: an explicit set is an override in force, an
    # inherit row means the override was closed on that date.
    if own is not None and not own.inherits_default:
        return ScheduleInForce(
            rest_weekdays=frozenset(own.rest_weekdays),
            effective_from=own.effective_from,
            inherited=False,
        )

    shared = await latest_rule(db, project_id=None, until=today)
    if shared is None:
        return ScheduleInForce(
            rest_weekdays=DEFAULT_REST_WEEKDAYS, effective_from=None, inherited=True
        )
    return ScheduleInForce(
        rest_weekdays=frozenset(shared.rest_weekdays),
        effective_from=shared.effective_from,
        inherited=True,
    )


async def set_override(
    db: AsyncSession,
    *,
    project_id: UUID,
    weekdays: frozenset[int],
    effective_from: date,
) -> None:
    """Append (or amend) the project's rule for one effective date.

    Same shape as the account default: one row per effective date, updated in
    place when the owner changes their mind on the same day.
    """
    rule = await db.scalar(
        select(ScheduleRule).where(
            ScheduleRule.project_id == project_id,
            ScheduleRule.effective_from == effective_from,
        )
    )
    if rule is None:
        db.add(
            ScheduleRule(
                project_id=project_id,
                rest_weekdays=sorted(weekdays),
                effective_from=effective_from,
            )
        )
    else:
        rule.rest_weekdays = sorted(weekdays)
        rule.inherits_default = False
    await db.commit()


async def clear_override(db: AsyncSession, *, project_id: UUID, today: date) -> None:
    """R14: close the override by appending, never by deleting.

    Removing the rows would resurrect days the owner had exempted, so the
    override stops with a row that inherits the account default from `today` —
    including whatever changes are made to that default later.
    """
    rule = await db.scalar(
        select(ScheduleRule).where(
            ScheduleRule.project_id == project_id,
            ScheduleRule.effective_from == today,
        )
    )
    if rule is None:
        db.add(
            ScheduleRule(
                project_id=project_id,
                rest_weekdays=[],
                effective_from=today,
                inherits_default=True,
            )
        )
    else:
        rule.inherits_default = True
        rule.rest_weekdays = []
    await db.commit()
