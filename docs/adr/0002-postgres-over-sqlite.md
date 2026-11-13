# PostgreSQL 16 for a single-user workload, over SQLite

The data volume and concurrency are small enough that SQLite would be entirely adequate — a few dozen writes a day, roughly 30k rows after three years. We chose Postgres anyway. The real reason is that the owner defined this as a proper project, and in a proper project the expensive cost is not query performance but **having to migrate the infrastructure six months in** because it was built too thin. Postgres brings JSON querying that needs no rewrite, `UNIQUE NULLS NOT DISTINCT` (which is exactly how `schedule_rule` enforces uniqueness per effective date), and native `uuid[]` / `inet` types — all of which would be string columns plus triggers on SQLite.

**Accepted cost, non-negotiable**: one more stateful container, one more password and connection pool to manage, one more upgrade path. In exchange we take on three constraints — every Alembic revision must be reversible, a daily `pg_dump` must reach off-machine storage, and images must pin a minor version rather than use `latest`.

**Options considered**: SQLite with WAL (zero ops, backup is copying a file); a managed Postgres service (an extra monthly bill for capabilities this workload never touches).
