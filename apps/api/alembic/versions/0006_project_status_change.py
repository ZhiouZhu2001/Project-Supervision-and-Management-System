"""project_status_change

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project_status_change",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("project.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'finished', 'archived')",
            name="ck_project_status_change_status",
        ),
    )
    op.create_index(
        "ix_project_status_change_project_effective",
        "project_status_change",
        ["project_id", "effective_from"],
    )

    # Existing projects get their first row, dated to when they started, so
    # their history is complete from the beginning rather than from today.
    op.execute(
        "INSERT INTO project_status_change (id, project_id, status, effective_from, created_at) "
        "SELECT gen_random_uuid(), id, status, created_business_date, now() FROM project"
    )


def downgrade() -> None:
    op.drop_index(
        "ix_project_status_change_project_effective", table_name="project_status_change"
    )
    op.drop_table("project_status_change")
