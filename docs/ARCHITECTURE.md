# Architecture

> Rule IDs (R1–R14) are defined in [`PRD.md`](PRD.md); terms in [`GLOSSARY.md`](../GLOSSARY.md). **This document is the single list of technical decisions**: when code disagrees with it, either the code changes or this document changes first, with a stated reason.

## 1. Shape

One VPS, five containers, one database, one disk. No cache layer, no message queue, no gateway software, no orchestrator. This is not a compromise — it is the correct shape for a single-user workload. The reasoning is in §10.

```
                ┌───────────────────────────────────────────────┐
  Browser / RN  │                    OVHcloud VPS (Ubuntu 24.04)│
      │         │  ┌─────────────────────────────────────────┐│
      │ HTTPS   │  │                nginx  :80/:443          ││
      └────────►│  │  /            → web:3000                ││
                │  │  /api/*       → api:8000                ││
                │  │  /uploads/*   → api:8000 (X-Accel)      ││
                │  └───────┬─────────────────────┬───────────┘│
                │          │                     │            │
                │   ┌──────▼──────┐      ┌───────▼─────────┐  │
                │   │  web        │      │  api            │  │
                │   │  Next.js 15 │─────►│  FastAPI        │  │
                │   │  stateless  │ int. │  uvicorn x1     │  │
                │   └─────────────┘      │  APScheduler    │  │
                │                        └───────┬─────────┘  │
                │                                │            │
                │                     ┌──────────▼─────────┐  │
                │                     │  db  PostgreSQL 16 │  │
                │                     │  volume: pgdata    │  │
                │                     └──────────┬─────────┘  │
                │                                │            │
                │   ┌──────────────┐   ┌─────────▼─────────┐  │
                │   │ uploads vol  │   │ backup (profile)  │  │
                │   │ /data/uploads│   │ pg_dump→restic→S3 │  │
                │   └──────────────┘   └───────────────────┘  │
                └───────────────────────────────────────────────┘
                                        │
                              OVH Object Storage (encrypted)
```

## 2. Components

| Component | Responsibility | Explicitly not |
|---|---|---|
| `nginx` | TLS termination, routing, rate limiting, compression, body-size limits | Business auth (only internal `X-Accel-Redirect` forwarding) |
| `web` (Next.js) | Rendering, forms, client state, SSR first paint | Any business-rule computation (invariant 12) |
| `api` (FastAPI) | All business rules, auth, validation, uploads, email, scheduled jobs | Rendering, templates, static assets |
| `db` (Postgres) | Persistence, constraints, uniqueness | Business logic in triggers or stored procedures |
| `backup` | Daily `pg_dump` + `uploads` increment + encrypted offsite upload | Running continuously (`profiles: ["ops"]`, triggered by cron) |

## 3. Deployment

### 3.1 Compose services

```yaml
services:
  nginx:   image: nginx:1.27-alpine      # the only service exposed to the internet
  web:     build: apps/web               # internal 3000
  api:     build: apps/api               # internal 8000, command runs --workers 1
  db:      image: postgres:16-alpine     # internal 5432, volume pgdata
  backup:  build: infra/backup           # profiles: ["ops"], invoked by host cron
```

- Every port binds `127.0.0.1`; only nginx binds publicly. **Never** `ports: - "5432:5432"`.
- Images pin a minor version (`postgres:16-alpine`, never `latest`); upgrading is an explicit act.
- `restart: unless-stopped`; healthchecks on `db` and `api`.
- Secrets live only in `.env` (`chmod 600` on the host), never in the compose file.

### 3.2 Volumes

| Volume | Mount | Backup |
|---|---|---|
| `pgdata` | `/var/lib/postgresql/data` | Daily `pg_dump` (logical, restorable across versions) |
| `uploads` | `/data/uploads` | Daily incremental `restic backup` |

### 3.3 nginx routing

```nginx
location /api/     { proxy_pass http://api:8000; }
location /uploads/ { proxy_pass http://api:8000; }   # api checks the session, then X-Accel-Redirect
location ~ ^/internal-uploads/ { internal; alias /data/uploads/; }
location /         { proxy_pass http://web:3000; }
client_max_body_size 6m;
limit_req zone=api burst=20 nodelay;                  # separate zone for /login
```

- Site-wide `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`.
- HTTP → HTTPS 301; Let's Encrypt certificates with scheduled renewal and `nginx -s reload`.
- A single entry point makes cookies same-origin, so **no CORS middleware is needed anywhere**.

### 3.4 Two base URLs for SSR

`web` needs two addresses; this is the one trap worth calling out:

- In the browser: `/api/...` (same origin, cookie attached automatically).
- During server-side rendering: `http://api:8000/...` (internal network, cookie forwarded manually).

Use `NEXT_PUBLIC_API_BASE=/api` and `INTERNAL_API_BASE=http://api:8000`, and branch on `typeof window === 'undefined'` inside `src/lib/api.ts`.

### 3.5 Environment variables

```ini
POSTGRES_DB=supervision
POSTGRES_USER=app
POSTGRES_PASSWORD=...
DATABASE_URL=postgresql+asyncpg://app:...@db:5432/supervision
APP_SECRET_KEY=...            # cookie signing
APP_BASE_URL=https://example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=...
SMTP_APP_PASSWORD=...         # Gmail app password; 2FA must be enabled
ALERT_RECIPIENT=...
OVH_S3_ENDPOINT=...
OVH_S3_BUCKET=...
OVH_S3_ACCESS_KEY=...
OVH_S3_SECRET_KEY=...
RESTIC_PASSWORD=...
```

## 4. Data model

Conventions: singular `snake_case` tables; `uuid` primary keys; every table has `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`; mutable tables add `updated_at`; user-data tables add `deleted_at` (soft delete).

### 4.1 `account` (ever exactly one row)

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `email` | `citext UNIQUE NOT NULL` | Sole login identifier |
| `password_hash` | `text NOT NULL` | argon2id |
| `display_name` | `text` | Shown next to the avatar and flame |
| `timezone` | `text NOT NULL DEFAULT 'Europe/Madrid'` | Constant, stored to avoid scattering it |
| `day_cutover_hour` | `smallint NOT NULL DEFAULT 4` | R1 |
| `alert_hour` | `smallint NOT NULL DEFAULT 21` | R12 |
| `created_at`, `updated_at` | `timestamptz` | |

> The global rest-day set is **not** here. It lives in `schedule_rule` as `project_id IS NULL`, so that R14's effective-date semantics apply uniformly.

### 4.2 `project`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `name` | `text NOT NULL` | 1–60 chars |
| `note` | `text` | Optional |
| `color`, `emoji` | `text` | Display only |
| `start_date` | `date NOT NULL` | May be past or future |
| `created_business_date` | `date NOT NULL` | Decides `counting_from` |
| `status` | `text NOT NULL DEFAULT 'active'` | `CHECK IN ('active','paused','finished','archived')`; a denormalised copy of the latest `project_status_change` |
| `finished_at`, `archived_at` | `timestamptz` | |
| `sort_order` | `int NOT NULL DEFAULT 0` | |
| `deleted_at` | `timestamptz` | Soft delete |

Indexes: `(status, deleted_at)`, `(sort_order)`.

### 4.3 `project_status_change` (R8/R10)

`id uuid PK`, `project_id uuid NOT NULL REFERENCES project ON DELETE CASCADE`, `from_status`, `to_status`, `effective_from date NOT NULL`, `reason text`, `created_at`.

Index: `(project_id, effective_from DESC)`. **Status on business day `D`** is the `to_status` of the latest row with `effective_from <= D`, defaulting to the initial `active`.

### 4.4 `schedule_rule` (R7/R14)

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `project_id` | `uuid NULL REFERENCES project ON DELETE CASCADE` | `NULL` = global default |
| `rest_weekdays` | `smallint[] NOT NULL` | ISO weekdays 1–7, unique elements |
| `effective_from` | `date NOT NULL` | |
| `created_at` | `timestamptz` | |

Constraint: `UNIQUE NULLS NOT DISTINCT (project_id, effective_from)` (Postgres 15+ syntax).

**Rest-day set on day `D`**: latest row with `project_id = P AND effective_from <= D`; else latest row with `project_id IS NULL AND effective_from <= D`; else `{6,7}`.

### 4.5 `log` (R2/R9)

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `project_id` | `uuid NOT NULL REFERENCES project ON DELETE CASCADE` | |
| `business_date` | `date NOT NULL` | Server-validated |
| `content` | `text NOT NULL` | 1–2000 chars |
| `duration_minutes` | `int NULL` | 0–1440 |
| `backfilled` | `bool NOT NULL DEFAULT false` | Server decides from `business_date < current business day` |
| `client_id` | `text NULL UNIQUE` | Idempotency key for offline replay (Phase 2) |
| `created_at`, `updated_at`, `deleted_at` | | |

Indexes: `(project_id, business_date) WHERE deleted_at IS NULL`, `(business_date) WHERE deleted_at IS NULL`.
**No** unique constraint on `(project_id, business_date)` — multiple logs per day are legal (R2).

### 4.6 `log_tag`

`(log_id uuid REFERENCES log ON DELETE CASCADE, tag text)`, primary key `(log_id, tag)`, tag ≤ 24 chars.

### 4.7 `attachment`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `log_id` | `uuid NOT NULL REFERENCES log ON DELETE CASCADE` | |
| `storage_key` | `text NOT NULL` | `YYYY/MM/<ulid>.<ext>`, never the original filename |
| `mime` | `text NOT NULL` | Sniffed server-side |
| `bytes` | `int NOT NULL` | ≤ 5 MB |
| `width`, `height` | `int` | Image metadata |
| `sha256` | `text NOT NULL` | Dedupe and integrity |
| `created_at` | `timestamptz` | |

### 4.8 `alert_log` (R12)

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid PK` | |
| `business_date` | `date NOT NULL UNIQUE` | Idempotency key |
| `outcome` | `text NOT NULL` | `sent` \| `skipped` \| `failed` |
| `project_ids` | `uuid[] NOT NULL DEFAULT '{}'` | Projects missed that round |
| `recipient` | `text` | |
| `error` | `text` | |
| `created_at` | `timestamptz` | |

**A row is written even when nothing is sent** (`skipped`). It doubles as proof the scheduler is alive, which is what `/api/healthz` reports.

### 4.9 `session`

`id uuid PK`, `account_id uuid`, `token_hash text UNIQUE`, `expires_at timestamptz`, `created_at`, `last_seen_at`, `user_agent text`, `ip inet`. Sliding 30-day expiry; `last_seen_at` updates at most once per 24 h. Deleting the row logs out.

## 5. Core algorithms

All live in `app/services/`, are pure functions where possible, and take an injectable clock so they can be unit tested.

### 5.1 Business day (`business_day.py`)

```python
def business_date_for(instant: datetime) -> date:
    """UTC instant → business day. R1: local time minus 4 hours, take the date."""
    local = instant.astimezone(MADRID)
    return (local - timedelta(hours=4)).date()

def business_day_bounds(d: date) -> tuple[datetime, datetime]:
    """Business day → [start_utc, end_utc); length may be 23, 24 or 25 hours."""
    start_local = datetime.combine(d, time(4, 0), tzinfo=MADRID)
    end_local = datetime.combine(d + timedelta(days=1), time(4, 0), tzinfo=MADRID)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)
```

The `ZoneInfo` object is constructed once at module scope. Never build it inside a loop.

### 5.2 Expected days (`business_day.py`)

```python
def expected_days(project, d_from: date, d_to: date) -> list[date]:
    """R3. Two queries (schedule_rule, project_status_change), then pure computation."""
    # 1) load both rule sets and status changes, ascending by effective_from
    # 2) for each day in [d_from, d_to]: >= counting_from, <= today,
    #    status == 'active', weekday not in rest_weekdays
```

The window is capped at 400 days. Beyond that, truncate and set `truncated: true` in the response — no real streak exceeds a year, and the cap bounds worst-case work.

### 5.3 Streak (`streak.py`, the only implementation)

```python
def current_streak(project, today: date, log_dates: set[date]) -> int:
    """R5. log_dates = every business day in the window with at least one log (one query)."""
    days = expected_days(project, today - timedelta(days=400), today)   # ascending, expected only
    checked = {d for d in days if d in log_dates}                       # logs on rest days never count
    if today in checked:
        idx = len(days) - 1
    else:
        idx = len(days) - 1 - (1 if days and days[-1] == today else 0)
    n = 0
    while idx >= 0 and days[idx] in checked:
        n += 1
        idx -= 1
    return n
```

Two queries total, no N+1. When a list page needs streaks for many projects, batch-load rules and logs for all of them and compute in Python — **never** call `current_streak` inside a loop that queries per project.

### 5.4 Calendar aggregation (`stats.py`)

At most 31 days × the number of active projects; aggregate in Python, no window functions:

```python
def month_grid(month: date, projects: list[Project], logs: list[Log]) -> list[DayCell]:
    # DayCell: business_date, expected_count, done_count, is_rest, state
    # state ∈ {'none','partial','most','all','rest','future'}
```

### 5.5 Alerts (`alerts.py`)

```python
def run_alert(business_date: date) -> AlertOutcome:
    """R12. Idempotency by pre-emption, not by check-then-act:
    INSERT ... ON CONFLICT (business_date) DO NOTHING RETURNING id.
    Only the caller that wins the insert proceeds."""
```

This survives restarts and overlapping runs; a read-then-insert would not.

## 6. API surface

Prefix `/api`. Every non-GET request validates the `Origin` header. Errors are `{"error":{"code","message","details"}}`.

| Method | Path | Notes |
|---|---|---|
| `POST` | `/auth/login` | `{email, password}` → sets cookie, returns the account |
| `POST` | `/auth/logout` | Deletes the current session |
| `POST` | `/auth/logout-all` | Deletes every session for the account |
| `GET` | `/auth/me` | Account + flame data |
| `GET` | `/projects/:id/schedule` | The rest-day rule in force for this project today, and whether it is inherited |
| `PUT` | `/projects/:id/schedule` | Sets or updates this project's override for an effective date |
| `DELETE` | `/projects/:id/schedule` | Drops the override so the project follows the account default |
| `GET` | `/settings` | The rest-day rule in force today, and the date it started |
| `PUT` | `/settings/rest-days` | Appends (or updates today's) rest-day rule; all seven days off is refused |
| `GET` | `/today` | The server's current business date, timezone, cutover hour, and every active project with its recorded state and latest entry |
| `GET` | `/projects` | List, filterable by `status`, includes `current_streak` and `longest_streak` |
| `POST` | `/projects` | `{name, start_date?, note?, rest_weekdays?}` |
| `GET` | `/projects/:id` | Detail + rates + schedule rule + status history |
| `PATCH` | `/projects/:id` | Name, note, colour, sort order only |
| `POST` | `/projects/:id/status` | `{to, effective_from?, reason?}`, validated by R8/R10 |
| `PUT` | `/projects/:id/schedule` | `{rest_weekdays, effective_from?}`; appends a rule (R14) |
| `DELETE` | `/projects/:id` | Soft delete; the project and its logs leave every view at once |
| `POST` | `/projects/:id/restore` | Undo a soft delete within thirty days, with logs and streak intact |
| `POST` | `/projects/:id/restore` | Undo soft delete within 30 days |
| `GET` | `/logs` | `?from&to&project_id&limit&cursor`, ordered `business_date DESC` |
| `POST` | `/logs` | `{project_id, business_date, content, duration_minutes?, tags?, client_id?}`; server derives `backfilled` |
| `PATCH` | `/logs/:id` | Body, duration, tags only — **not** `business_date` or `project_id` |
| `DELETE` | `/logs/:id` | Soft delete |
| `POST` | `/logs/:id/attachments` | `multipart/form-data`, ≤ 5 MB each, ≤ 4 per log |
| `DELETE` | `/attachments/:id` | Soft-delete metadata, delete the file asynchronously |
| `GET` | `/calendar` | `?month=YYYY-MM` (defaults to the current business month) → per-day expected/done counts and a state bucket |
| `GET` | `/stats` | Four metrics: per-project rates, current + longest streak, 12-week rollup, 30-day log count |
| `GET` | `/export.json` | Full export: projects, logs, tags, attachment metadata, schedule rules, status changes |
| `GET` | `/healthz` | Public, unauthenticated: `{db, last_alert_business_date, version}` |
| `GET` | `/uploads/*` | Session check, then `X-Accel-Redirect` |

**Changing a log's date is not an edit — it is delete plus backfill.** `PATCH` refuses `business_date`, which makes R9's window and per-day limit impossible to bypass.

## 7. Authentication and sessions

- Single user: the `account` row is created from `.env` at boot. No registration endpoint exists.
- Passwords: `argon2id` via `argon2-cffi` at library-default parameters (time_cost=3, memory_cost=64 MiB).
- Login rate limit: nginx `limit_req zone=login burst=5`; five consecutive failures lock for 15 minutes (in-memory counter; resetting on restart is acceptable).
- Sessions: 32 random bytes; the DB stores `sha256(token)`. Cookie `sid` is `HttpOnly; Secure; SameSite=Lax; Path=/`, sliding 30-day expiry.
- CSRF: `SameSite=Lax` plus `Origin` validation on non-GET requests. No CSRF token — the benefit doesn't justify the machinery.
- Logout deletes the row; "log out everywhere" deletes all rows.

## 8. File storage

- Upload: `api` receives → validates `Content-Type` and actual bytes (open with Pillow and `verify()`) → computes `sha256` → writes `/data/uploads/YYYY/MM/<ulid>.<ext>` → inserts the `attachment` row. **Disk first, DB second**; a DB failure deletes the file.
- Read: `GET /uploads/<key>` → session check → `X-Accel-Redirect: /internal-uploads/<key>`, so Python never buffers the file.
- Limits: 5 MB per file, 4 per log, 50 GB soft cap overall.
- Cleanup: a daily job hard-deletes files and rows 30 days after soft delete.

## 9. Backup and restore

- Daily 03:30 host cron: `pg_dump -Fc` → temp file → `restic backup` (encrypted) → OVH Object Storage.
- The `uploads` volume is backed up the same way, incrementally.
- Retention: 7 daily, 4 weekly, 12 monthly (`restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12`).
- **Quarterly drill**: `make restore f=<snapshot>` into a clean compose stack, then `make test-api`. A backup that has never been restored is not a backup.
- RPO 24 h, RTO 1 h — acceptable for one machine and one user.

## 10. Deliberately not built

Each entry states the condition that would reopen it. Without that trigger, it does not get added.

| Not built | Why | Reconsider when |
|---|---|---|
| **Redis / any cache** | QPS < 1; queries under 10 ms; invalidation logic is pure liability | Home page P95 > 300 ms with DB CPU persistently > 50% |
| **API gateway (Kong/APISIX/Traefik plugins)** | nginx already routes, terminates TLS and rate-limits | Per-consumer auth policy or dynamic multi-service routing is needed |
| **Message queue (RabbitMQ/Kafka/Celery+broker)** | One async job, already idempotent | A second async job appears, or callbacks / long-running tasks arrive |
| **Microservices** | Four service classes; splitting buys network and deployment cost | More than 3 contributors and merge conflicts become the bottleneck |
| **Kubernetes / Nomad** | One machine | Horizontal scaling or canary releases are needed |
| **CDN** | One user reaching his own VPS from Spain | Users span continents and static assets become the bottleneck |
| **Full-text search (ES / pg_trgm)** | ~30k rows over three years; `ILIKE` is fine | More than 100k logs and search exceeds 200 ms |
| **Event sourcing / CQRS** | Only one status chain, already logged as changes | Replay, audit or multiple read models become necessary |
| **Multi-tenancy (`tenant_id` / RLS)** | Exactly one user | A second person actually uses it — write an ADR first |
| **Chart library** | Four numbers on `/stats`; plain CSS suffices | A trend chart is needed beyond the calendar heat map |
| **Internationalisation** | One language, one timezone | A second language is required |
| **Sentry / APM** | Logs plus `/healthz` cover a single-user system | An error appears that cannot be reproduced from logs |
| **GraphQL / tRPC / generated SDK** | REST plus hand-written types; 30 endpoints | More than 80 endpoints and type drift causes real defects |

## 11. Capacity budget

| Quantity | Estimate | Basis |
|---|---|---|
| Projects | ≤ 30 | Upper bound for one person to maintain |
| Logs | 30 × 365 ≈ 11k/year, ≈ 33k over 3 years | One per project per day at most, typically |
| Attachments | ≤ 20 GB over 3 years | One 2 MB image per log |
| Database | < 1 GB | 33k rows of text |
| Peak QPS | < 5 | One user |
| Page P95 | < 300 ms (same region) | |
| Host size | 2 vCPU / 4 GB / 80 GB SSD | Includes Postgres and backup staging |

## 12. Observability

- All containers log JSON to stdout; `docker compose logs` is the whole truth. nginx keeps its own access log.
- `/api/healthz` reports DB connectivity and `last_alert_business_date`; host cron curls it every 5 minutes and emails after six consecutive failures (reusing the SMTP config).
- The scheduler always writes an `alert_log` row, including `skipped`, which distinguishes "nothing was missed" from "the scheduler is dead".

## 13. Roadmap

| Phase | Scope | Exit condition |
|---|---|---|
| **1** | FastAPI + responsive Next.js (installable to home screen), all of R1–R14, email alerts, backups | PRD acceptance criteria met; 14 days of use without a streak error |
| **2** | React Native (Expo): today / quick log / project detail only; offline queue with `client_id` idempotency | 30 days of web use confirms those three screens are the whole need |
| **3** | Only against demonstrated pain: trends, reports, richer export | The owner asks for it |
