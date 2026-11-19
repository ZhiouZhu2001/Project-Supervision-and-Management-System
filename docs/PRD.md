# PRD · Project Supervision and Management System

> Terminology lives in [`GLOSSARY.md`](../GLOSSARY.md). The rule IDs below (R1–R14) are cited directly by code comments and test cases. **Changing a rule means changing every site that cites its ID.**

## One sentence

Turn "what did I actually do today" into a queryable fact, and wake the owner up with red status plus an email on the days he should have logged and didn't.

## The owner and three moments

There is exactly one user — the owner. The product's value concentrates in three moments of the day:

| Moment | What he's doing | What the system must give |
|---|---|---|
| Daytime or late night | Logging something in passing | One field, one pick, save, gone — under 10 seconds |
| Before bed | Wondering whether today counts | A single unambiguous "logged / not logged" |
| Next morning | Opening the app to see yesterday | Red status, break notice, and "how far back can I still backfill" |

## Non-goals

Explicitly out of scope. Anything landing here gets discussed before it is built:

- Multiple users, registration, invitations, collaboration, shared projects.
- Tasks, to-dos, boards, Gantt charts, sub-item hierarchies.
- Timer-based time tracking — there is no start/stop clock.
- Social features on check-ins: scores, friends, leaderboards, sharing.
- Native mobile apps (Phase 2), desktop apps, browser extensions.
- General note-taking, knowledge base, backlinks.
- Analytics dashboards, generated weekly reports, AI summaries (Phase 3 at the earliest).
- Syncing with any third party (calendar, GitHub, health data) — **not in Phase 1**.
- Internationalisation: English UI, one timezone.

## Core objects

```
Project
  ├─ status: active ─┬─> paused ──> active
  │                  ├─> finished   (terminal; not reversible)
  │                  └─> archived <──> active   (reversible)
  ├─ start_date
  ├─ schedule rules (rest weekdays) with effective dates
  └─ Log × N   —— each attached to one project and one business day
```

**Finished is irreversible** and must be confirmed explicitly by the owner. **Archived is reversible** and can return to active at any time. Neither state raises alerts or contributes to active statistics.

## Business rules

### R1 · Business day

A business day is the 24-hour window `[04:00, next 04:00)` in `Europe/Madrid`. Its date is the calendar date of the starting instant: `2026-03-10 02:30` belongs to business day `2026-03-09`.

- The timezone is fixed to `Europe/Madrid` and is not configurable.
- Daylight saving is handled by calendar day, not by elapsed hours: the business day of `2026-03-28` lasts 23 h and the one of `2026-10-24` lasts 25 h. The short or long day is the one the clock change falls inside, which is the day *before* the switch date, because a business day runs 04:00 to 04:00.
- All business-day computation happens server-side; client-supplied dates are validated (invariant 1 in AGENTS.md).

### R2 · Log

A log is `project + business day + body`, with optional `duration_minutes`, `tags[]` and `images[]`.

- A project may have **multiple logs on the same business day**.
- Body is required, 1–2000 characters; duration is 0–1440 minutes.
- A log and a check-in are the same thing: a log means checked in (see R4).

### R3 · Expected day

Business day `D` is an expected day for project `P` if and only if all of the following hold:

1. `D >= counting_from(P)`, where `counting_from(P) = max(P.start_date, P.created_business_date)`;
2. `D <= current business day`;
3. `P`'s status on `D` is `active`;
4. `D`'s weekday is not in the rest-day set in effect on `D` (see R7).

Clause 1 means **history before the project existed never counts**. Setting a start date in the past is allowed — for the honest case "I've been at this for three months" — but the system will not manufacture a backlog of shame.

### R4 · Check-in and miss

- **Checked in**: project `P` has at least one non-deleted log on business day `D`.
- **Miss**: `D` is an expected day with no log. A miss is **never stored**; it is computed at query time, so there are no negative records to undo.

### R5 · Streak

For project `P` on the current business day `T`:

```
anchor = T                if T is an expected day AND T is checked in
         most recent expected day strictly before T   otherwise
streak = walk backwards from anchor through the sequence of expected days,
         counting checked-in days until the first unchecked expected day
```

- Non-expected days (rest days, paused periods, dates after finishing or archiving, dates before creation) are **skipped**: they neither add to the count nor break the chain.
- Not having logged `T` **is not a miss** — the day isn't over, so it cannot break the chain.
- Streaks are computed per project and never interact.

### R6 · Break and longest streak

- `break`: a miss on an expected day resets the project's current streak to 0; the next expected day starts again at 1.
- `longest_streak`: the all-time maximum, **never decreases**, and backfilling does not increase it (see R9).

### R7 · Rest days

- Global default: an account-level setting, default Saturday and Sunday (`[6,7]`, ISO weekdays).
- Project override: a single project may override the global setting; without an override it inherits.
- Rules carry `effective_from` and apply only from that date onward — **never retroactively**. Changing a rest day today cannot break or resurrect last year's streak.
- Rest days require no log, add nothing to a streak, raise no alerts, and render with a neutral background in the calendar.

### R8 · Pause

- While `paused`, days are not expected days: no alerts, excluded from completion-rate denominators, and the streak freezes (neither grows nor decays).
- Resuming to `active` continues from the frozen value.
- Pause boundaries are business-day granular and must go through the status endpoint; the column is never edited directly.

### R9 · Backfill

- Writing a log is allowed for any of the past `7` business days (`D >= current business day − 7`); older dates are rejected with 422.
- At most `3` backfilled logs per project per business day; the excess is rejected with 422.
- Backfilled logs carry `backfilled = true`, decided by the server from `D < current business day`; clients cannot set it.
- **Backfilling does not repair the streak and does not raise `longest_streak`.** It only affects the total completion rate.

### R10 · Finish and archive

- `finished`: requires a second confirmation; afterwards the streak is frozen permanently, the project moves to the completed list, and it raises no alerts.
- `archived`: freely toggles with `active`. While archived it raises no alerts and contributes to no statistic.
- Soft delete: `DELETE /projects/:id` sets `deleted_at`; after 30 days a cleanup job hard-deletes the project, its logs and its images.

### R11 · Flame

When the largest current streak across all `active` projects is `>= 7`, the avatar shows `🔥 ×N` where N is that maximum; tapping or hovering reveals the project name. When the maximum drops, the flame disappears.

### R12 · Miss alert

- Runs once daily at `21:00` Europe/Madrid.
- Detection: the set `M` of `active` projects where `T` is an expected day and there is no log.
- If `M` is non-empty, send **one** digest email; if empty, send nothing.
- The email lists each project's name, current streak, consecutive missed days, and a direct link.
- **Idempotent**: `alert_log` is unique per business day, so a re-run never double-sends.
- Failures retry 3 times with exponential backoff; then log and give up without blocking other jobs or surfacing an error to the owner.
- Consecutive missed days **do not** trigger escalating emails.

### R13 · Statistics

For project `P` over `[D1, D2]`:

```
expected set E = { D ∈ [D1,D2] | D is an expected day for P }
completion_rate       = |{D ∈ E | checked in}| / |E|
clean_completion_rate = |{D ∈ E | at least one non-backfilled log}| / |E|
```

- When the denominator is 0, both rates are `null` (rendered as "—"), not 0 and not 100%.
- Calendar day ratio = checked-in active projects / expected active projects that day, bucketed into `0 / (0,0.5] / (0.5,1) / 1`; a zero denominator renders neutral.

### R14 · Schedule rule changes

Any change to "which weekdays are rest days" appends a history row carrying `effective_from`; existing rows are never modified. Streak and rate computation looks up the rule in effect on each business day. This is the implementation constraint behind R7 and the only place a historical version is permitted.

## User stories

1. On my phone, I can record "2 h writing code" in under 10 seconds and immediately see today as logged.
2. I remember at 23:50 and log — it still counts as today (the business day runs to 04:00).
3. I write at 02:00 and it lands on yesterday; if yesterday was a miss, it's now filled but marked as backfilled.
4. I sleep through the weekend; Monday shows both days as rest days and my streak is intact.
5. I travel for a week and pause the project; when I return the streak is exactly where I left it.
6. I forget for three days and receive three emails (one per day), each naming the projects that broke.
7. I want to fill in the day before yesterday; the system allows it (within 7 days), but the streak still restarts from today.
8. I finish a project; it moves to completed and the flame recalculates over the remaining active projects.
9. I delete a project by accident and can restore it within 30 days.
10. I change my rest days and last year's streak does not move.

## Page list (Phase 1)

| Route | Content |
|---|---|
| `/login` | Email + password; no registration entry point |
| `/` | Today cards (one row per active project, logged / not logged), global month calendar, flame, red banner |
| `/projects` | Project list grouped by status, with current streak |
| `/projects/:id` | Detail: streak bar, rates, schedule rule, status actions, log timeline |
| `/projects/new` | Create: name, start date, optional rest-day override |
| `/logs/new` | Quick log (project + body) |
| `/calendar` | Full-screen month calendar; tap a day to see its logs |
| `/stats` | Four metrics (see R13 and ARCHITECTURE) |
| `/settings` | Email, password, global rest days, alert time (read-only: fixed 21:00), export, backup status |

The Phase 2 React Native client covers exactly three screens: today, quick log, project detail. Nothing else.

## Edge cases (each must have a test)

1. Month boundary: `2026-03-31 03:59` and `04:01` fall on different business days.
2. DST transitions: the business day of `2026-03-28` is 23 h and the one of `2026-10-24` is 25 h; streaks don't jump.
3. Creation day: `counting_from = creation business day`; the creation day is itself an expected day.
4. Start date in the past: days before creation count toward nothing.
5. Pause on the current day: takes effect the same day per `effective_from`.
6. Resume day: the resume day is an expected day again.
7. Changing rest days: historical streaks and rates are unchanged.
8. Backfill 8 days ago: rejected. Fourth backfill on one day: rejected.
9. Streak after backfilling: unchanged; `longest_streak`: unchanged.
10. Logging right after the 21:00 alert: the email already went out (not recalled) but the next day's computation is unaffected.
11. All projects archived: flame disappears, no alert sent.
12. Two logs submitted concurrently for the same project and day: both succeed (no unique constraint) and both count.
13. Empty body / oversized body / oversized duration: 422.
14. Display timezone: stored in UTC, rendered in Europe/Madrid; travelling to another timezone still computes business days in Madrid.

## Acceptance criteria (end of Phase 1)

- All 14 edge cases above have passing tests.
- From opening the page to a saved log takes ≤ 10 seconds on a mobile connection (walkthrough, not a perf test).
- 14 consecutive days of personal use with no streak computation error, verified by manual spot-check of three random projects.
- Backups are real: pull the latest snapshot from OVH Object Storage, restore into an empty database, run `make test` against it.
- `make lint && make test` green.
