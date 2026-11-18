"""Status resolution (R8/R10/R14) as a pure function.

The "no rows" case is load-bearing: migration 0006 deliberately seeds no
history, so a project that never changed status must still read as active on
every day of its life.
"""

from datetime import date

import pytest

from app.services.status import can_transition, status_on

TODAY = date(2026, 11, 18)


def test_a_project_with_no_history_is_active_from_the_beginning() -> None:
    # This is what lets 0006 stay schema-only: R3's counting_from already
    # excludes the days before the project existed.
    assert status_on(date(2020, 1, 1), []) == "active"
    assert status_on(TODAY, []) == "active"


def test_the_latest_rule_on_or_before_the_day_wins() -> None:
    rules = [(date(2026, 1, 1), "paused"), (date(2026, 6, 1), "active")]

    assert status_on(date(2025, 12, 31), rules) == "active"
    assert status_on(date(2026, 1, 1), rules) == "paused"
    assert status_on(date(2026, 5, 31), rules) == "paused"
    assert status_on(date(2026, 6, 1), rules) == "active"


def test_a_rule_effective_tomorrow_does_not_apply_today() -> None:
    # R14: a change never reaches backwards.
    rules = [(date(2026, 11, 19), "paused")]

    assert status_on(TODAY, rules) == "active"


@pytest.mark.parametrize(
    ("current", "target", "allowed"),
    [
        ("active", "paused", True),
        ("active", "archived", True),
        ("paused", "active", True),
        ("archived", "active", True),
        ("archived", "paused", False),
        ("finished", "active", False),
        ("finished", "archived", False),
        ("finished", "finished", False),
        ("active", "active", False),
    ],
)
def test_the_state_machine(current: str, target: str, allowed: bool) -> None:
    assert can_transition(current, target) is allowed
