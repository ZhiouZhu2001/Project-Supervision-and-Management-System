from datetime import UTC, date, datetime, timedelta

import pytest

from app.services.business_day import (
    BusinessDateError,
    business_date_for,
    business_day_bounds,
    validate_business_date,
)


def test_just_before_the_cutover_belongs_to_the_previous_day() -> None:
    # 03:59 Europe/Madrid in winter is 02:59 UTC.
    instant = datetime(2026, 11, 15, 2, 59, tzinfo=UTC)

    assert business_date_for(instant) == date(2026, 11, 14)


def test_exactly_at_the_cutover_belongs_to_the_new_day() -> None:
    # 04:00 Europe/Madrid in winter is 03:00 UTC.
    instant = datetime(2026, 11, 15, 3, 0, tzinfo=UTC)

    assert business_date_for(instant) == date(2026, 11, 15)


def test_bounds_of_an_ordinary_day_are_twenty_four_hours() -> None:
    start, end = business_day_bounds(date(2026, 11, 15))

    assert end - start == timedelta(hours=24)
    assert start == datetime(2026, 11, 15, 3, 0, tzinfo=UTC)


def test_the_spring_forward_day_is_twenty_three_hours() -> None:
    # The switch happens at 02:00 on 29 March, between the 04:00 cutovers of
    # the 28th and the 29th — so the 23-hour business day is the 28th.
    start, end = business_day_bounds(date(2026, 3, 28))

    assert end - start == timedelta(hours=23)


def test_the_autumn_back_day_is_twenty_five_hours() -> None:
    # Symmetrically, the 25-hour business day is 24 October.
    start, end = business_day_bounds(date(2026, 10, 24))

    assert end - start == timedelta(hours=25)


def test_a_spring_forward_instant_still_lands_on_the_right_day() -> None:
    # 05:00 local on the switch day is 03:00 UTC (CEST, +2).
    instant = datetime(2026, 3, 29, 3, 0, tzinfo=UTC)

    assert business_date_for(instant) == date(2026, 3, 29)


def test_today_is_accepted_by_the_shared_validation() -> None:
    today = date(2026, 11, 17)

    assert validate_business_date(today, today=today) == today


def test_a_past_date_is_accepted_by_the_shared_validation() -> None:
    today = date(2026, 11, 17)

    assert validate_business_date(today - timedelta(days=3), today=today) == today - timedelta(
        days=3
    )


def test_a_future_date_is_rejected_with_a_stable_code() -> None:
    today = date(2026, 11, 17)

    with pytest.raises(BusinessDateError) as raised:
        validate_business_date(today + timedelta(days=1), today=today)

    assert raised.value.code == "BUSINESS_DATE_IN_FUTURE"
