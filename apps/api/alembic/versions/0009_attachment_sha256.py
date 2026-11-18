"""attachment.sha256

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable: rows written before this revision have no digest, and the
    # export states that rather than inventing one.
    op.add_column("attachment", sa.Column("sha256", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("attachment", "sha256")
