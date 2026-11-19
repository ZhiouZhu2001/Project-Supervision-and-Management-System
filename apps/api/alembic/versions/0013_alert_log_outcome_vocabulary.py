"""alert_log: the outcome vocabulary is the documented one

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-19

Revision 0012 renamed the column but not the check constraint behind it, so
`skipped` and `pending` were rejected by a constraint still enforcing the old
`no_misses` word — which stopped the application from starting, because the
digest claims its day at boot. The constraint is recreated under the new name
and with the documented values. Schema only, reversible (invariant 11).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_VALUES = "'sent', 'skipped', 'failed', 'pending'"


def upgrade() -> None:
    op.drop_constraint("ck_alert_log_status", "alert_log", type_="check")
    op.create_check_constraint("ck_alert_log_outcome", "alert_log", f"outcome IN ({NEW_VALUES})")


def downgrade() -> None:
    # The narrower constraint is not restored. It would reject the `skipped`
    # and `pending` rows written since, and mapping them back to `no_misses`
    # is a data move that belongs in its own revision, not here (invariant 11).
    op.drop_constraint("ck_alert_log_outcome", "alert_log", type_="check")
