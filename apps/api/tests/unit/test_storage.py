"""Storage naming (ARCH 8, AGENTS security).

The name on disk must be a ULID under `YYYY/MM`, never anything derived from
the uploaded file: a filename is user input and a stable one leaks content.
"""

import io
import re
from datetime import UTC, date, datetime, timedelta

from PIL import Image

from app.services.storage import save_image
from app.ulid import _ALPHABET, new_ulid

ULID_PATH = re.compile(r"^\d{4}/\d{2}/([0-9A-HJKMNP-TV-Z]{26})\.(png|jpg|webp)$")


def _png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 6), "#b84c25").save(buffer, format="PNG")
    return buffer.getvalue()


def test_a_stored_image_is_named_by_a_ulid_under_year_and_month() -> None:
    stored = save_image(_png(), today=date(2026, 11, 19))

    match = ULID_PATH.match(stored.storage_path)
    assert match is not None, stored.storage_path
    assert stored.storage_path.startswith("2026/11/")


def test_a_ulid_is_twenty_six_crockford_characters() -> None:
    value = new_ulid()

    assert len(value) == 26
    assert set(value) <= set(_ALPHABET)


def test_two_ulids_are_unique_even_in_the_same_millisecond() -> None:
    assert len({new_ulid() for _ in range(1000)}) == 1000


def test_ulids_sort_by_the_instant_they_were_minted() -> None:
    early = new_ulid(datetime(2026, 11, 19, 10, 0, tzinfo=UTC))
    later = new_ulid(datetime(2026, 11, 19, 10, 0, tzinfo=UTC) + timedelta(minutes=1))

    assert early < later

