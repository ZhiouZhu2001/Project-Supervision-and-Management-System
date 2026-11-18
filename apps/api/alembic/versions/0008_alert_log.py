"""alert_log

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alert_log",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("project_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('sent', 'no_misses', 'failed')", name="ck_alert_log_status"
        ),
    )
    op.create_index("ix_alert_log_business_date", "alert_log", ["business_date"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_alert_log_business_date", table_name="alert_log")
    op.drop_table("alert_log")
