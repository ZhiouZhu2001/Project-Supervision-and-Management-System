#!/bin/sh
# Dump, encrypt, upload, prune — and leave a status file behind whatever
# happens. A backup that fails silently is indistinguishable from one that
# never ran, so every exit path writes its verdict.
set -eu

STATUS_DIR="${STATUS_DIR:-/data/backup-status}"
STATUS_FILE="$STATUS_DIR/status.json"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
WORK="$(mktemp -d)"
KEEP_DAILY="${BACKUP_KEEP_DAILY:-7}"
KEEP_WEEKLY="${BACKUP_KEEP_WEEKLY:-4}"
KEEP_MONTHLY="${BACKUP_KEEP_MONTHLY:-12}"

mkdir -p "$STATUS_DIR"

write_status() {
    # $1 ok|failed, $2 detail
    printf '{"at":"%s","ok":%s,"detail":"%s","repository":"%s"}\n' \
        "$STAMP" "$1" "$2" "${RESTIC_REPOSITORY:-none}" > "$STATUS_FILE"
}

fail() {
    write_status false "$1"
    echo "backup failed: $1" >&2
    rm -rf "$WORK"
    exit 1
}

[ -n "${RESTIC_REPOSITORY:-}" ] || fail "RESTIC_REPOSITORY is not set"
[ -n "${RESTIC_PASSWORD:-}" ] || fail "RESTIC_PASSWORD is not set"

echo "dumping database"
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges \
    | gzip -9 > "$WORK/database.sql.gz" || fail "pg_dump failed"

if [ -d /data/uploads ]; then
    echo "archiving uploads"
    tar -czf "$WORK/uploads.tar.gz" -C /data uploads || fail "uploads archive failed"
fi

echo "encrypting and uploading"
restic snapshots >/dev/null 2>&1 || restic init >/dev/null || fail "restic init failed"
restic backup --tag daymark "$WORK" || fail "restic backup failed"

echo "pruning"
restic forget --tag daymark \
    --keep-daily "$KEEP_DAILY" \
    --keep-weekly "$KEEP_WEEKLY" \
    --keep-monthly "$KEEP_MONTHLY" \
    --prune || fail "restic forget failed"

write_status true "ok"
rm -rf "$WORK"
echo "backup complete"
