from datetime import UTC

from app.clock import now_utc


def test_now_utc_is_aware_and_in_utc() -> None:
    moment = now_utc()
    assert moment.tzinfo is not None
    assert moment.utcoffset() == UTC.utcoffset(None) or moment.utcoffset().total_seconds() == 0
