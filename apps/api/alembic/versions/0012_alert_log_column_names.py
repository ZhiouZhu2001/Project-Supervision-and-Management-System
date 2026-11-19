"""alert_log: outcome / project_ids / recipient / error

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-19

ARCH 4.8 declares these columns. `status` was the same idea under another name,
`detail` was `error`, and the digest kept only a count of the projects it named
instead of their ids — the one piece of information that makes a sent message
auditable later. Schema only, reversible (invariant 11).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("alert_log", "status", new_column_name="outcome")
    op.alter_column("alert_log", "detail", new_column_name="error")
    op.add_column(
        "alert_log",
        sa.Column(
            "project_ids",
            postgresql.ARRAY(sa.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column("alert_log", sa.Column("recipient", sa.String(length=255), nullable=True))
    op.drop_column("alert_log", "project_count")


def downgrade() -> None:
    op.add_column(
        "alert_log",
        sa.Column("project_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_column("alert_log", "recipient")
    op.drop_column("alert_log", "project_ids")
    op.alter_column("alert_log", "error", new_column_name="detail")
    op.alter_column("alert_log", "outcome", new_column_name="status")
