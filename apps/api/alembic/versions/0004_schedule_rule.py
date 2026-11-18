"""schedule_rule

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedule_rule",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("project.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("rest_weekdays", postgresql.ARRAY(sa.SmallInteger()), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # NULLS NOT DISTINCT (Postgres 15+) makes "one global rule per date" a real
    # constraint: project_id is null for the account-wide default.
    op.execute(
        "CREATE UNIQUE INDEX ix_schedule_rule_unique "
        "ON schedule_rule (project_id, effective_from) NULLS NOT DISTINCT"
    )
    op.create_index(
        "ix_schedule_rule_project_effective", "schedule_rule", ["project_id", "effective_from"]
    )


def downgrade() -> None:
    op.drop_index("ix_schedule_rule_project_effective", table_name="schedule_rule")
    op.drop_index("ix_schedule_rule_unique", table_name="schedule_rule")
    op.drop_table("schedule_rule")
