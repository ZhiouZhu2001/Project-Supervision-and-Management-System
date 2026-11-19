from datetime import date, timedelta

from app.services.streak import (
    consecutive_misses,
    current_streak,
    expected_days,
    longest_streak,
)

# 2024-01-01 is a Monday, which keeps weekday reasoning explicit.
MONDAY = date(2024, 1, 1)
WEEKEND = frozenset({6, 7})


def day(offset: int) -> date:
    return MONDAY + timedelta(days=offset)


def test_no_expected_days_is_zero() -> None:
    assert current_streak([], set(), MONDAY) == 0


def test_a_recorded_today_is_a_streak_of_one() -> None:
    days = expected_days(day(0), day(0))

    assert current_streak(days, {day(0)}, day(0)) == 1


def test_consecutive_days_counted_backwards() -> None:
    days = expected_days(day(-3), day(0))
    checked = {day(-3), day(-2), day(-1), day(0)}

    assert current_streak(days, checked, day(0)) == 4


def test_a_gap_stops_the_count() -> None:
    days = expected_days(day(-4), day(0))
    # day(-3) is missing.
    checked = {day(-4), day(-2), day(-1), day(0)}

    assert current_streak(days, checked, day(0)) == 3


def test_today_unrecorded_does_not_break_the_chain() -> None:
    days = expected_days(day(-2), day(0))
    checked = {day(-2), day(-1)}

    # The day is not over; only completed days can break a chain.
    assert current_streak(days, checked, day(0)) == 2


def test_today_unrecorded_with_yesterday_missing_is_zero() -> None:
    days = expected_days(day(-2), day(0))
    checked = {day(-2)}

    assert current_streak(days, checked, day(0)) == 0


def test_rest_days_are_skipped_rather_than_broken() -> None:
    # Monday to the following Monday, with Saturday and Sunday off.
    days = expected_days(day(0), day(7), rest_weekdays=WEEKEND)
    checked = {day(0), day(1), day(2), day(3), day(4), day(7)}

    assert [d for d in days] == [day(0), day(1), day(2), day(3), day(4), day(7)]
    assert current_streak(days, checked, day(7)) == 6


def test_a_rest_day_does_not_add_to_the_count() -> None:
    days = expected_days(day(0), day(7), rest_weekdays=WEEKEND)
    checked = {day(6), day(7)}

    # Saturday is a rest day, so it is invisible either way.
    assert current_streak(days, checked, day(7)) == 1


def test_the_first_expected_day_starts_the_count() -> None:
    days = expected_days(day(0), day(0))

    assert current_streak(days, {day(0)}, day(0)) == 1
    assert current_streak(days, set(), day(0)) == 0


def test_longest_streak_keeps_the_best_run() -> None:
    days = expected_days(day(-6), day(0))
    # Three in a row, a gap, then two.
    checked = {day(-6), day(-5), day(-4), day(-2), day(-1)}

    assert longest_streak(days, checked) == 3


def test_longest_streak_of_nothing_is_zero() -> None:
    assert longest_streak(expected_days(day(0), day(0)), set()) == 0


def test_longest_streak_survives_a_later_break() -> None:
    # Five good days, then nothing. The current streak is 0, but the record
    # of what was achieved must not disappear (R6).
    days = expected_days(day(-10), day(0))
    checked = {day(-10), day(-9), day(-8), day(-7), day(-6)}

    assert current_streak(days, checked, day(0)) == 0
    assert longest_streak(days, checked) == 5


def test_consecutive_misses_counts_expected_days_since_the_last_record() -> None:
    days = [day(0), day(1), day(2)]

    assert consecutive_misses(days, {day(0)}) == 2


def test_a_project_never_recorded_has_a_run_the_length_of_its_history() -> None:
    assert consecutive_misses([day(0), day(1)], set()) == 2


def test_a_project_recorded_on_the_latest_day_has_no_run() -> None:
    assert consecutive_misses([day(0), day(1)], {day(1)}) == 0


def test_rest_days_and_pauses_are_invisible_to_the_run() -> None:
    # A gap in the calendar is not a gap in the record: the expected-day list
    # simply has no entry for a rest day or a paused stretch (R7, R8).
    days = [day(0), day(7)]

    assert consecutive_misses(days, {day(0)}) == 1
