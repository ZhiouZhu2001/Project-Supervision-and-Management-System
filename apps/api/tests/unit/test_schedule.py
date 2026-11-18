from datetime import date, timedelta

import pytest

from app.services.schedule import (
    DEFAULT_REST_WEEKDAYS,
    rest_weekdays_for,
    validate_rest_weekdays,
)

MONDAY = date(2024, 1, 1)


def day(offset: int) -> date:
    return MONDAY + timedelta(days=offset)


def test_the_default_is_the_weekend() -> None:
    assert frozenset({6, 7}) == DEFAULT_REST_WEEKDAYS
    assert rest_weekdays_for(day(0), []) == DEFAULT_REST_WEEKDAYS


def test_a_rule_applies_from_its_effective_date() -> None:
    rules = [(day(2), frozenset({1}))]

    assert rest_weekdays_for(day(1), rules) == DEFAULT_REST_WEEKDAYS
    assert rest_weekdays_for(day(2), rules) == frozenset({1})


def test_a_later_rule_takes_over() -> None:
    rules = [(day(0), frozenset({5})), (day(7), frozenset({3, 4}))]

    assert rest_weekdays_for(day(3), rules) == frozenset({5})
    assert rest_weekdays_for(day(7), rules) == frozenset({3, 4})
    assert rest_weekdays_for(day(20), rules) == frozenset({3, 4})


def test_a_rule_dated_in_the_future_does_not_affect_today() -> None:
    rules = [(day(30), frozenset({1}))]

    assert rest_weekdays_for(day(0), rules) == DEFAULT_REST_WEEKDAYS


def test_a_mid_history_change_does_not_rewrite_the_past() -> None:
    # Rest days were the weekend, then changed to Wednesdays on day 10.
    rules = [(day(10), frozenset({3}))]

    assert rest_weekdays_for(day(9), rules) == DEFAULT_REST_WEEKDAYS
    assert rest_weekdays_for(day(10), rules) == frozenset({3})


def test_every_weekday_can_be_expected() -> None:
    assert validate_rest_weekdays([]) == frozenset()


def test_all_seven_rest_days_is_refused() -> None:
    with pytest.raises(ValueError):
        validate_rest_weekdays([1, 2, 3, 4, 5, 6, 7])


def test_weekday_numbers_must_be_iso_range() -> None:
    with pytest.raises(ValueError):
        validate_rest_weekdays([0, 3])
    with pytest.raises(ValueError):
        validate_rest_weekdays([1, 8])


def test_duplicates_are_collapsed() -> None:
    assert validate_rest_weekdays([6, 7, 6]) == frozenset({6, 7})
