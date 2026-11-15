"""account, session, project

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=16), nullable=True),
        sa.Column("emoji", sa.String(length=8), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("created_business_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active','paused','finished','archived')", name="ck_project_status"
        ),
    )
    op.create_index("ix_project_status_deleted_at", "project", ["status", "deleted_at"])
    op.create_index("ix_project_sort_order", "project", ["sort_order"])


def downgrade() -> None:
    op.drop_index("ix_project_sort_order", table_name="project")
    op.drop_index("ix_project_status_deleted_at", table_name="project")
    op.drop_table("project")
