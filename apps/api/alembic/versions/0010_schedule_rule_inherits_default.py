"""schedule_rule.inherits_default

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # R14: closing a per-project override has to be an appended row, not a
    # deletion, or the days the old rule governed would change meaning. A row
    # with this flag set means "follow the account default from here".
    op.add_column(
        "schedule_rule",
        sa.Column(
            "inherits_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("schedule_rule", "inherits_default")
