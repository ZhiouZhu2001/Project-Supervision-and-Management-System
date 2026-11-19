"""attachment: storage_path -> storage_key, content_type -> mime, byte_size -> bytes

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-19

ARCH 4.7 names these columns; the implementation had drifted to three other
names. Renaming is schema-only (invariant 11) and reversible.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RENAMES = (
    ("storage_path", "storage_key"),
    ("content_type", "mime"),
    ("byte_size", "bytes"),
)


def upgrade() -> None:
    for old, new in RENAMES:
        op.alter_column("attachment", old, new_column_name=new)


def downgrade() -> None:
    for old, new in RENAMES:
        op.alter_column("attachment", new, new_column_name=old)
