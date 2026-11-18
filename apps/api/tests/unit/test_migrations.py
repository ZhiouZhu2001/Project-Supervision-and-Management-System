"""Invariant 11, checked against the migrations themselves.

Two properties are only observable in `alembic/versions`, so they get a guard
here rather than a database test:

* every revision implements `downgrade()`, so a rollback is always possible;
* no revision both changes schema and moves data — rolling a table back must
  never be the thing that silently discards rows, and a data migration must
  never be what created the table it writes to.
"""

import ast
import re
from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"

# Calls that change the schema. `op.execute` is deliberately absent: it is DDL
# half the time (the NULLS NOT DISTINCT index), so the DML check below looks at
# the SQL text instead of the call.
DDL_CALLS = {
    "create_table",
    "drop_table",
    "add_column",
    "drop_column",
    "alter_column",
    "create_index",
    "drop_index",
    "create_unique_constraint",
    "drop_constraint",
    "create_foreign_key",
    "rename_table",
}

DML_PATTERN = re.compile(r"\b(INSERT\s+INTO|DELETE\s+FROM|UPDATE\s+\w+\s+SET)\b", re.IGNORECASE)


def _revisions() -> list[tuple[str, str]]:
    paths = sorted(VERSIONS.glob("*.py"))
    assert paths, f"no revisions found under {VERSIONS}"
    return [(path.name, path.read_text(encoding="utf-8")) for path in paths]


def test_every_revision_is_reversible() -> None:
    for name, source in _revisions():
        functions = {
            node.name for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)
        }
        assert "downgrade" in functions, f"{name} has no downgrade()"


def test_no_revision_both_changes_schema_and_moves_data() -> None:
    for name, source in _revisions():
        touches_schema = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in DDL_CALLS
            for node in ast.walk(ast.parse(source))
        )
        moves_data = DML_PATTERN.search(source) is not None
        assert not (touches_schema and moves_data), (
            f"{name} both changes schema and moves data; split it into a schema "
            f"revision and a data revision"
        )
