# AGENTS.md

The contract for AI agents working in this repository. Humans should start at [`docs/PRD.md`](docs/PRD.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Terminology defers to [`GLOSSARY.md`](GLOSSARY.md) — **code identifiers, UI copy, API names and comments all use the words defined there.**

## What this is

A single-user **self-supervision system**. The owner logs what he did each day against a handful of projects; the system derives streaks from those logs and raises red status plus an email on any day that should have a log and doesn't.

**It is not**: a team tool, a task manager, a multi-tenant SaaS, a construction/engineering supervision system, a time tracker, or a note-taking app. Any request pushing it in those directions gets checked against the Non-goals section of the PRD first.

## Current status

**Phase 0 — documents only. There is no application code yet.** Everything under `apps/` and `infra/` is a plan, not an implementation.

Next steps, in order: build the schema from ARCHITECTURE §4, the API surface from §6, then the web screens from the PRD page list.

Phase 1 is web-first. The React Native client is Phase 2: **do not scaffold anything for it now**, but keep the API contract client-agnostic.

All repository artifacts — documents, code, comments, commit messages, UI strings — are written in **English**. Conversation with the owner follows his language.

---

## Invariants

Each one is testable. An implementation that violates any of them is incomplete regardless of whether the feature "works".

1. **Business days are computed server-side only.** Clients send a `YYYY-MM-DD` `business_date`; the server validates it via `app/services/business_day.py` — not a future business day, not earlier than `counting_from = max(project.start_date, project.created_business_date)`, not earlier than current business day − 7. Clients **never** compute "today".
2. **`backfilled` is decided by the server**: `business_date < current business day`. Any client-supplied `backfilled` value is ignored.
3. **Exactly one streak implementation**: `app/services/streak.py`. Everything that needs a streak calls it. Reimplementing it in SQL, in the frontend or in a script is forbidden.
4. **Backfill window is 7 days, max 3 backfilled logs per project per business day.** Over the limit returns 422 — not 400, not silent truncation.
5. **Recording friction is a product constraint, not a UI preference.** The quick-log form has exactly two required fields: project and body. Adding a third required field requires a written justification in the change description.
6. **Alerts are idempotent**: `alert_log.business_date` is unique, so the alert job can be re-run without double-sending.
7. **Times are stored as `timestamptz` in UTC**, business days as `date`. The DB session timezone is UTC; display converts to Europe/Madrid. **`datetime.now()` is banned** — use `now_utc()` / `today_business_date()` from `app/clock.py`, which tests can inject.
8. **Single-process assumption**: `uvicorn --workers 1`. The scheduler is in-process APScheduler. No second scheduler, no distributed lock.
9. **No cache layer, no message queue, no API gateway software, no service mesh, no Kubernetes.** See "Deliberately not built" in the architecture doc.
10. **Passwords use argon2id**; sessions use httpOnly + Secure + SameSite=Lax cookies, with only a hash of the token stored server-side.
11. **Every migration is reversible**: each Alembic revision implements `downgrade()`, and no revision both changes schema and moves data.
12. **The frontend computes no business rules.** Completion rates, streaks and miss detection all come from the API. The client renders and does optimistic updates, nothing more.

---

## Stack (locked)

Changing a row here requires an ADR and the owner's agreement. Do **not** swap anything for "more modern" or "simpler".

| Layer | Choice |
|---|---|
| Runtime | Python 3.12 / Node.js 22 LTS |
| API framework | FastAPI + Pydantic v2 |
| ORM / migrations | SQLAlchemy 2.0 (async, asyncpg) / Alembic |
| Database | PostgreSQL 16 |
| Background jobs | APScheduler, in-process, single instance |
| Package managers | `uv` (Python) / `pnpm` (Node) |
| Web | Next.js 15 App Router + TypeScript (strict) |
| Styling | Tailwind CSS + shadcn/ui |
| Client state | zustand — UI state only |
| Server state | TanStack Query v5 — the only data-fetching path |
| Charts | none yet |
| Reverse proxy | nginx |
| Orchestration | Docker Compose |
| Host | OVHcloud VPS / Ubuntu 24.04 LTS |
| Tests | pytest + pytest-asyncio + httpx (API) / Vitest (web) |
| Mobile (Phase 2) | React Native + Expo |

**Never introduce**: Redux, Prisma, TypeORM, GraphQL, tRPC, Server Actions that write to the DB, Sentry (revisit in Phase 3), a second design system alongside shadcn, or any CRUD scaffold generator.

---

## Repository layout

```
.
├── AGENTS.md                    # this file
├── GLOSSARY.md                  # domain vocabulary, sole source of truth
├── README.md
├── docs/
│   ├── PRD.md                   # rules R1–R14, stories, acceptance
│   ├── ARCHITECTURE.md          # topology, schema, API, deployment, non-goals
│   ├── adr/
│   ├── specs/                   # one spec per deliverable slice
│   └── tickets/                 # one file per ticket, numbered in dependency order
├── docker-compose.yml           # nginx / web / api / db / backup
├── docker-compose.dev.yml       # dev overrides: hot reload, exposed ports
├── Makefile                     # the only documented entry point for commands
├── .env.example
├── apps/
│   ├── api/
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── alembic/versions/
│   │   ├── app/
│   │   │   ├── main.py          # assembly, middleware, error handling
│   │   │   ├── config.py        # pydantic-settings
│   │   │   ├── clock.py         # now_utc / today_business_date (injectable)
│   │   │   ├── db.py            # engine, session, dependency
│   │   │   ├── models/          # SQLAlchemy models, one file per table
│   │   │   ├── schemas/         # Pydantic request/response
│   │   │   ├── routers/         # auth, projects, logs, calendar, stats, files
│   │   │   ├── services/
│   │   │   │   ├── business_day.py   # business days, rest days, expected days
│   │   │   │   ├── streak.py         # streaks — the only implementation
│   │   │   │   ├── alerts.py         # miss detection, email rendering, delivery
│   │   │   │   └── stats.py          # rates, calendar aggregation
│   │   │   ├── jobs/scheduler.py     # APScheduler wiring (21:00 alert)
│   │   │   └── security.py           # passwords, sessions, dependencies
│   │   └── tests/
│   │       ├── unit/                 # pure functions: business_day, streak, stats
│   │       └── api/                  # httpx against the app
│   └── web/
│       ├── package.json
│       ├── src/app/                  # App Router: login, (app), projects, settings
│       ├── src/components/
│       ├── src/lib/api.ts            # typed fetch wrapper
│       ├── src/lib/business-day.ts   # display formatting only, no rules
│       ├── src/stores/               # zustand
│       └── src/hooks/                # TanStack Query hooks
└── infra/
    ├── nginx/                      # site config, TLS, rate limits
    ├── backup/                     # pg_dump + object storage + restore scripts
    └── scripts/                    # bootstrap
```

Every new directory must belong to one of the above. Do not create directories "for later".

---

## Commands

Everything runs through `make`; never document long `docker compose` invocations.

```
make dev            # dev environment (Postgres + hot reload)
make down           # stop
make migrate        # alembic upgrade head
make migration m="" # generate a migration (edit downgrade by hand)
make test           # api + web tests
make test-api       # pytest
make test-web       # vitest
make lint           # ruff + tsc --noEmit
make fmt            # ruff format + prettier
make shell-api      # shell into the api container
make psql           # psql session
make backup         # run a backup now
make restore f=...  # restore from backup (destructive, interactive confirm)
```

`make lint && make test` must pass before every commit.

---

## Git workflow

The remote is `origin` → `https://github.com/ZhiouZhu2001/Project-Supervision-and-Management-System.git`. The owner requires work to reach `main` continuously: **every completed slice is committed and pushed, not batched.**

**A slice** is the smallest change that leaves the repository self-consistent — a document section, a schema migration with its tests, one working endpoint, one screen. If you stop mid-slice, you are not done.

- **Trunk-based.** Commit directly to `main`. Do not open branches, and do not open pull requests unless the owner asks.
- **Push immediately after committing.** Never leave committed work unpushed at the end of a turn.
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`. Subject in imperative English, ≤ 72 characters, no trailing period.
- **The body explains why**, and cites the rule or decision it implements — `Refs R5`, `See ADR 0003`.
- **Never** force-push `main`, rewrite pushed history, commit `.env` or any secret, commit generated artifacts (`node_modules`, `.next`, `__pycache__`, `.venv`), or bypass hooks with `--no-verify`.
- **This Windows machine needs `git config http.sslBackend openssl`** — schannel fails to negotiate TLS here. It is already set in the local repo config; do not remove it.
- **If a push fails for credentials, stop and report it.** Do not invent a token, do not switch the remote to a different protocol, do not ask for a password in a commit message.

A slice counts as delivered only when `git status` is clean and `origin/main` matches `HEAD`.

---

## Code conventions

**Python**: ruff owns formatting and imports; full type annotations (mypy-strict friendly); services never import FastAPI and never take a `Request` — routers only validate and translate; all DB access goes through SQLAlchemy, no string-concatenated SQL.

**TypeScript**: `strict: true`, no `any` (use `unknown` plus narrowing); components never call `fetch` directly — go through the typed functions in `src/lib/api.ts`; server state lives only in TanStack Query, zustand holds only UI state (is a dialog open, which day is selected).

**Naming**: DB tables are `snake_case` and singular (`project`, `log`, `attachment`); Python classes PascalCase, functions snake_case; TS components PascalCase, hooks `useXxx`; API paths are plural nouns in kebab-case.

**Comments** explain *why*, not *what*. Any comment touching time, timezones or streaks cites its rule — e.g. `# R7: rest days do not break the chain`.

---

## Data and API conventions

- All endpoints live under `/api`. Versioning is additive-only; there is no `/v1` because there is one controlled client.
- Errors are `{"error": {"code": "...", "message": "...", "details": {...}}}`; `code` is a stable machine-readable string.
- Pagination is `?cursor=&limit=`, used only by `/api/logs` and calendar endpoints — the dataset is small.
- Field naming: `created_at` / `updated_at` are UTC timestamps; `business_date` is a date; `*_on` is a date, `*_at` is a timestamp.
- Deletes are soft (`deleted_at`) with physical deletion after 30 days by a cleanup job; `DELETE` returns 204.

---

## Security and privacy

This is diary-grade data; treat it accordingly.

- HTTPS everywhere, automatic renewal; HTTP 301s to HTTPS.
- Only 80/443 exposed; SSH key-only; UFW + fail2ban; container ports bound to `127.0.0.1`.
- Uploads accept `image/jpeg|png|webp` only, verified by sniffing actual bytes, ≤ 5 MB, random ULID filenames — never the user's original filename.
- Logs and error messages must never contain passwords, cookies, or log bodies. The body appears in exactly one structured field.
- Backups contain everything, so they are encrypted (restic) and stored off the machine.

---

## When to write an ADR

Only when all three hold: hard to reverse, surprising without context, and the result of a real trade-off. One or two paragraphs is the right length — the value is recording that a decision was made and why.

On file: `0001-record-is-checkin`, `0002-postgres-over-sqlite`, `0003-business-day-0400-madrid`.

**No ADR needed** for a new column, a copy change, an icon, or a library you could swap in a week.

---

## Definition of Done

A slice is done only when all of these hold:

1. The behaviour maps to a PRD rule ID (R1–R14); if it doesn't, change the PRD first.
2. `make lint && make test` is green; changes to `business_day`, `streak` or `stats` have unit tests covering the boundaries (month end, DST, rest days, paused periods, backfill).
3. Every new or changed endpoint is reflected in the API table in the architecture doc.
4. Nothing from the "Deliberately not built" list has been added.
5. User-facing copy is English and uses glossary terms.
6. Committed with a conventional message, pushed to `origin/main`.

---

## Working with the owner

- The owner is the only user and the only product decision-maker. **Architecture and implementation details are yours to decide; product semantics and rule changes are his.**
- When a requirement is ambiguous, don't guess and don't dump ten questions: give 2–4 options, a recommendation, and the reasoning.
- Any change that makes logging more expensive (another required field, another tap, another confirm) is rejected by default — cite invariant 5.
- Don't ask "shall I continue?" or "is this ok?" — those carry no information. Do the work, then report the result and the risks.
