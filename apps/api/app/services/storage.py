"""Where uploads live and how they are named.

Two rules govern everything here:

* the type is decided by **decoding** the bytes, never by the declared content
  type or the filename extension;
* the name on disk is random and partitioned by month, so two concurrent
  uploads cannot collide and an old file is easy to find.
"""

import contextlib
import io
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from app.config import get_settings

MAX_BYTES = 5 * 1024 * 1024
MAX_PER_LOG = 4

# Format -> (content type, extension). Pillow reports the real format after
# parsing the bytes, so a .png that is really a JPEG is stored as a JPEG.
FORMATS: dict[str, tuple[str, str]] = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


class UnsupportedImage(ValueError):
    pass


@dataclass
class StoredImage:
    storage_path: str
    content_type: str
    byte_size: int
    width: int
    height: int


def upload_root() -> Path:
    return Path(get_settings().upload_dir)


def inspect_image(data: bytes) -> tuple[str, int, int]:
    """Return (content type, width, height) for a decodable JPEG/PNG/WebP."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = image.format or ""
            width, height = image.size
            # full decode: a truncated or crafted file must not slip through
            image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise UnsupportedImage("not a decodable image") from exc

    if image_format not in FORMATS:
        raise UnsupportedImage(f"{image_format or 'unknown'} is not an accepted format")
    if width <= 0 or height <= 0:
        raise UnsupportedImage("image has no pixels")

    return FORMATS[image_format][0], width, height


def save_image(data: bytes, *, today) -> StoredImage:
    content_type, width, height = inspect_image(data)
    extension = FORMATS[next(key for key, value in FORMATS.items() if value[0] == content_type)][1]

    relative = f"{today.year:04d}-{today.month:02d}/{uuid4().hex}{extension}"
    absolute = upload_root() / relative
    absolute.parent.mkdir(parents=True, exist_ok=True)

    # "x" fails instead of overwriting: a collision must be an error, not a
    # silent replacement of somebody else's file.
    with absolute.open("xb") as handle:
        handle.write(data)

    return StoredImage(
        storage_path=relative,
        content_type=content_type,
        byte_size=len(data),
        width=width,
        height=height,
    )


def delete_image(storage_path: str) -> None:
    """Remove a stored file, tolerating one that is already gone.

    A missing file must not fail a delete that already removed the row; the
    cleanup job can still reconcile the directory later.
    """
    with contextlib.suppress(OSError):
        (upload_root() / storage_path).unlink(missing_ok=True)
