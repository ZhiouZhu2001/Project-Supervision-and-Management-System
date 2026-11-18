"""attachment

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachment",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "log_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("log.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(length=160), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_attachment_log_id", "attachment", ["log_id"])
    op.create_index("ix_attachment_storage_path", "attachment", ["storage_path"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_attachment_storage_path", table_name="attachment")
    op.drop_index("ix_attachment_log_id", table_name="attachment")
    op.drop_table("attachment")
