# Backup and restore

The diary is not reproducible. Everything else on this host can be rebuilt from
git, but a lost database is a lost year.

## What runs

The `backup` service dumps the database, archives the image store, encrypts
both with restic and pushes the encrypted snapshot to `RESTIC_REPOSITORY` — a
different machine, in the normal case an S3-compatible bucket. It runs at 03:00
Europe/Madrid and recomputes that time each loop, so a restart does not shift
the schedule.

Retention is applied by the same run:

| Kept | Count |
|---|---|
| Daily | 7 |
| Weekly | 4 |
| Monthly | 12 |

`restic forget --keep-* --prune` removes everything older, so the repository
does not grow without bound.

Every run — successful or not — writes `/data/backup-status/status.json`:

```json
{"at":"2026-11-18T10:55:40Z","ok":true,"detail":"ok","repository":"/repo"}
```

`/api/healthz` returns that file as `last_backup`. A backup that stops running
therefore looks like a defect from outside, which is the only way a silent
backup failure ever gets noticed.

## Restoring

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backup /usr/local/bin/restore.sh
```

It takes the newest snapshot by default, or a snapshot id as its argument. It
loads the dump into `POSTGRES_DB` and untars the images into the uploads
volume. It is destructive on purpose: it replaces what is there.

## Drill — 2026-11-18

Performed on the development stack, because that is the stack that exists
before the host does. The same image and the same two scripts are used in
production; only the restic repository differs.

**Data present**: 3 projects, 3 logs, 3 status rows, 1 schedule rule, 1 image.

| Step | Command | Result |
|---|---|---|
| Backup | `backup.sh` against the live database | snapshot `0c061822`, `keep 1 snapshots`, exit 0 |
| Status file | read from the status volume | `{"ok":true,"detail":"ok"}` |
| Target | create an empty `supervision_restored` database | empty |
| Restore | `restore.sh` with `POSTGRES_DB=supervision_restored` | `Restored 4 files/dirs`, exit 0 |
| Row counts | compare source and restored | both `projects=3 logs=3 statuses=3 rules=1` |
| Content | `md5(string_agg(content \|\| business_date))` | `dfe35d633226b4361aa863d9975eedd9` on both |
| Images | second pass with one attachment | 1 file restored in the uploads volume, 1 attachment row |
| Suite | `pytest` with `TEST_DATABASE_URL` pointing at the restored database | all tests pass |

**Duration**: backup ≈ 3 s, restore ≈ 2 s at this data size. Both are dominated
by container start-up; the dump itself is milliseconds. This is not a
prediction for a year of data — the monthly drill is where that gets measured.

**Surprises, recorded because they are the point of a drill**

1. The first pass restored a database with zero images, because the uploads
   volume happened to be empty. The tar round-trip "worked" without testing
   anything. A second pass with a real attachment was run; only then did the
   archive contain a file. A drill that passes against empty data proves
   nothing about the data path.
2. `restore.sh` into a non-empty database silently conflicts rather than
   replacing rows. The production procedure is: create the database, then
   restore into it. The script is not a migration tool.
3. `pg_dump` runs with `--no-owner --no-privileges`: a restore into a stack with
   different role names must not fail on ownership it does not need.

## What this does not cover

The restic repository in the drill was a local volume, not an offsite bucket.
The encryption and the restore path are exercised; the offsite hop is the same
`restic backup` call with a different `RESTIC_REPOSITORY` URL, and it is the one
step that only the real host can prove.
