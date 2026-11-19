"""The columns ARCH 4.7 declares, checked against the models.

The architecture document is the single list of technical decisions, so a
model that quietly renames a column makes the document wrong for everyone who
reads it later. These tests fail on a rename instead of two years of drift.
"""

from app.models.attachment import Attachment


def test_attachment_columns_are_the_ones_the_architecture_declares() -> None:
    assert set(Attachment.__table__.columns.keys()) == {
        "id",
        "log_id",
        "storage_key",
        "mime",
        "bytes",
        "width",
        "height",
        "sha256",
        "created_at",
        # Soft delete: AGENTS requires it on every user-data table, so it is
        # present even though ARCH 4.7 lists only the domain columns.
        "deleted_at",
    }
