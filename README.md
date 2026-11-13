# Project Supervision and Management System

A single-user **self-supervision system**. You log what you actually did each day against a small set of projects; the system derives your streaks from those logs, and when a day that should have a log has none, it says so — loudly, in red, and by email.

It exists for one failure mode: the quiet drift where nobody is watching, so nothing gets done.

**Status: Phase 0 — design only. No application code yet.**

## What it is not

Not a team tool, not a task manager, not a multi-tenant SaaS, not a time tracker, not a note-taking app. It has exactly one user and no registration flow.

## Stack

| Layer | Choice |
|---|---|
| API | Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic |
| Database | PostgreSQL 16 |
| Web | Next.js 15 (App Router) · TypeScript · Tailwind · shadcn/ui · TanStack Query · zustand |
| Background jobs | APScheduler (in-process, single instance) |
| Proxy / TLS | nginx · Let's Encrypt |
| Runtime | Docker Compose on an OVHcloud VPS, Ubuntu 24.04 LTS |
| Mobile (Phase 2) | React Native · Expo |

Deliberately absent: Redis, message queue, API gateway, Kubernetes, microservices, multi-tenancy. Each omission has an explicit re-evaluation trigger in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#10-deliberately-not-built).

## Repository layout

```
AGENTS.md            Agent contract: invariants, stack, commands, DoD
GLOSSARY.md          Domain vocabulary — the single source of truth for terms
docs/PRD.md          Business rules R1–R14, user stories, edge cases, acceptance
docs/ARCHITECTURE.md Topology, schema, algorithms, API, deployment
docs/adr/            Decision records
apps/api/            FastAPI service          (Phase 1)
apps/web/            Next.js client           (Phase 1)
infra/               nginx, backup, bootstrap (Phase 1)
```

## Documentation map

Start with [`AGENTS.md`](AGENTS.md) if you are an agent, or [`docs/PRD.md`](docs/PRD.md) if you are a human. Terminology in every document defers to [`GLOSSARY.md`](GLOSSARY.md).

Locked decisions worth knowing before reading code:

- [ADR 0001](docs/adr/0001-record-is-checkin.md) — a check-in *is* a log; there is no separate check-in entity.
- [ADR 0002](docs/adr/0002-postgres-over-sqlite.md) — Postgres 16 despite a single-user workload.
- [ADR 0003](docs/adr/0003-business-day-0400-madrid.md) — a business day runs 04:00 → 04:00 Europe/Madrid, and is not configurable.

## Roadmap

| Phase | Scope | Exit condition |
|---|---|---|
| 0 | Design documents (this commit) | Rules R1–R14 agreed |
| 1 | API + responsive web app, all rules, email alerts, backups | Acceptance criteria in PRD met; 14 days of personal use with no streak error |
| 2 | React Native client (today / quick log / project detail) | 30 days of web use confirming those three screens are all that's needed |
| 3 | Only on demonstrated pain: trends, reports | User asks for it |

## Development

Commands are not final until the Phase 1 scaffold lands. Local requirements: Docker Compose, `make`, and — on this Windows machine specifically — `git config http.sslBackend openssl`, because schannel fails to negotiate TLS here.

## License

MIT — see [`LICENSE`](LICENSE).
