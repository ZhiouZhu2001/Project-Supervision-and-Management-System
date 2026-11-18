"""Read the backup sidecar's verdict.

The backup container writes a small JSON file after every run, whether it
worked or not. Reading it here is what turns "no backup happened" from an
invisible fact into a health-endpoint answer.
"""

import json
from pathlib import Path

from app.config import get_settings


def read_backup_status() -> dict | None:
    path = Path(get_settings().backup_status_file)
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None
