"""log_tag

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "log_tag",
        sa.Column(
            "log_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("log.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("tag", sa.String(length=24), primary_key=True),
        sa.CheckConstraint("length(tag) BETWEEN 1 AND 24", name="ck_log_tag_length"),
    )


def downgrade() -> None:
    op.drop_table("log_tag")
