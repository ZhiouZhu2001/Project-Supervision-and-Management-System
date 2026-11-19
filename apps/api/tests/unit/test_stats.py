"""The arithmetic behind /stats, tested without a database.

R13 defines the rates over an explicit expected-day set; the week buckets are
the one place a boundary can be off by a day, so both are pinned here.
"""

from datetime import date, timedelta

from app.services.stats import ProjectRates, week_start

# Monday.
MONDAY = date(2026, 11, 16)


def test_a_week_starts_on_its_monday() -> None:
    assert week_start(MONDAY) == MONDAY
    assert week_start(MONDAY + timedelta(days=3)) == MONDAY
    assert week_start(MONDAY + timedelta(days=6)) == MONDAY


def test_sunday_belongs_to_the_week_that_started_six_days_before() -> None:
    sunday = MONDAY + timedelta(days=6)

    assert week_start(sunday) == MONDAY


def test_a_week_spanning_new_year_keeps_its_monday() -> None:
    # 2026-12-31 is a Thursday; its week starts on Monday the 28th.
    assert week_start(date(2026, 12, 31)) == date(2026, 12, 28)
    assert week_start(date(2027, 1, 1)) == date(2026, 12, 28)


def _rates(expected: int, recorded: int, clean: int) -> ProjectRates:
    return ProjectRates(
        project=None,  # type: ignore[arg-type]
        expected=expected,
        recorded=recorded,
        clean=clean,
        current_streak=0,
        longest_streak=0,
    )


def test_rates_are_checked_in_days_over_all_expected_days() -> None:
    rates = _rates(expected=4, recorded=3, clean=1)

    assert rates.completion_rate == 0.75
    assert rates.clean_completion_rate == 0.25


def test_a_project_that_expected_nothing_reports_null_not_zero() -> None:
    # R13: a zero denominator is "no data", never "nothing was done".
    rates = _rates(expected=0, recorded=0, clean=0)

    assert rates.completion_rate is None
    assert rates.clean_completion_rate is None
