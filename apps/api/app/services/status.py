"""Which status was in force on a given day (R14).

A project is only "expected" on days when it was active. Pausing therefore
does not need a special case in the streak kernel: the paused days simply
leave the expected list, the chain closes over the gap, and resuming
continues from the same number.
"""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.status import ProjectStatusChange

StatusRule = tuple[date, str]


def status_on(day: date, rules: Sequence[StatusRule], default: str = "active") -> str:
    """Rules must be ascending by effective date; the latest one wins."""
    chosen = default
    for effective_from, status in rules:
        if effective_from > day:
            break
        chosen = status
    return chosen


def status_resolver(rules: Sequence[StatusRule], default: str = "active"):
    def current_status(day: date) -> str:
        return status_on(day, rules, default)

    return current_status


def can_transition(current: str, target: str) -> bool:
    """Guard the state machine.

    Finishing is terminal through the interface (ticket 19): a finished project
    is a statement that the work is done, and ticket 20 is explicit that it
    cannot even be filed away afterwards. Archiving is the reversible one, so
    it is the only status that can come back.
    """
    if current == "finished":
        return False
    if current == target:
        return False
    if current == "archived":
        return target == "active"
    return target in {"active", "paused", "finished", "archived"}


async def load_status_rules(db: AsyncSession, *, until: date) -> dict[UUID, list[StatusRule]]:
    """Status history per project, ascending, up to `until` inclusive.

    Ordering by creation time inside a day is what makes a pause and a resume
    on the same day resolve in the order they happened.
    """
    rows = await db.scalars(
        select(ProjectStatusChange)
        .where(ProjectStatusChange.effective_from <= until)
        .order_by(ProjectStatusChange.effective_from, ProjectStatusChange.created_at)
    )
    grouped: dict[UUID, list[StatusRule]] = {}
    for row in rows:
        grouped.setdefault(row.project_id, []).append((row.effective_from, row.status))
    return grouped
