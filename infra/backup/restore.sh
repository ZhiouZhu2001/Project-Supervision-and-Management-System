#!/bin/sh
# Rebuild a stack from the newest (or a named) snapshot.
#
# Destructive by design: it replaces the database and the image store. The
# drill in docs/BACKUP.md runs exactly this script, so what is written down is
# what has actually been executed.
set -eu

SNAPSHOT="${1:-latest}"
WORK="$(mktemp -d)"

[ -n "${RESTIC_REPOSITORY:-}" ] || { echo "RESTIC_REPOSITORY is not set" >&2; exit 1; }

echo "restoring $SNAPSHOT into $WORK"
restic restore "$SNAPSHOT" --target "$WORK" || { echo "restore failed" >&2; exit 1; }

DUMP="$(find "$WORK" -name database.sql.gz | head -1)"
[ -n "$DUMP" ] || { echo "no database dump in the snapshot" >&2; exit 1; }

echo "loading the database"
gunzip -c "$DUMP" | PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --quiet >/dev/null

UPLOADS="$(find "$WORK" -name uploads.tar.gz | head -1)"
if [ -n "$UPLOADS" ]; then
    echo "restoring uploads"
    tar -xzf "$UPLOADS" -C /data
fi

rm -rf "$WORK"
echo "restore complete"
