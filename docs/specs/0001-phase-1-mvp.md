# Spec 0001 — Phase 1 MVP: the self-supervision loop

Status: ready-for-agent
Scope: Phase 1 of [the roadmap](../ARCHITECTURE.md#13-roadmap)
Vocabulary: [`GLOSSARY.md`](../../GLOSSARY.md) — every noun below is a defined term

## Problem Statement

The owner starts things constantly and finishes very few of them. The failure is never a dramatic decision to quit; it is a quiet week where nothing gets written down, and because nothing is written down there is no record, and because there is no record nothing corrects him.

Every tool he has tried fails the same way: recording costs more than the work it is meant to record. A tracker wanting a start button, a stop button and a category asks for six interactions to capture something that took ten seconds; a task board asks him to maintain a backlog he does not want; a notebook has no memory. Within two weeks the tool is abandoned, and its abandonment is invisible — which is exactly the condition it was supposed to detect.

So the problem is not "where do I write things down". It is: **there is no cheap way to record a day, and no loud signal when a day goes unrecorded.** A quiet omission is indistinguishable from a good week, and that ambiguity is what lets the drift continue.

## Solution

A single-user web application with one job: make recording a day trivial, and make a missing day impossible to ignore.

He opens the app, picks a project, types one line, and is done — under ten seconds, on a phone, with nothing else required. In exchange, the system keeps count: every project carries its own streak of consecutive expected days; rest days he configures do not break it; a project he pauses freezes it; a day he skips breaks it and cannot be repaired by backfilling later, only recorded honestly.

When a day that should have been recorded passes without a record, the system says so twice. Once at 21:00 in an email naming the projects he missed, and once the next time he opens the app, in red, with the streak reset and the calendar showing the hole.

The product's promise is narrow and it should stay narrow: it remembers so he does not have to, and it does not let him look away.

## User Stories

### Getting in

1. As the owner, I want to set my email and password once during setup, so that the app is mine and nobody else's.
2. As the owner, I want to log in with email and password, so that I do not depend on a third-party identity provider to reach my own data.
3. As the owner, I want my session to last 30 days without re-authenticating, so that logging a thought never costs a login.
4. As the owner, I want to log out, and to log out every device at once, so that a lost phone does not mean a lost diary.
5. As the owner, I want repeated failed logins to be throttled, so that a public endpoint does not become a guessing game.

### Projects

6. As the owner, I want to create a project with a name and a start date, so that the thing I intend to keep doing exists somewhere.
7. As the owner, I want the creation day to count as the project's first expected day, so that a new project starts working immediately.
8. As the owner, I want to backdate a project's start date to before I created it, so that an effort already underway can be adopted honestly.
9. As the owner, I do not want backdating to create a backlog of misses, so that starting a project never begins with a wall of red.
10. As the owner, I want to rename, recolour and reorder projects, so that the list stays legible as it grows.
11. As the owner, I want to see every project's current streak in one list, so that I can tell at a glance which one is slipping.
12. As the owner, I want projects grouped by active, paused, finished and archived, so that abandoned things stop competing for attention.

### Recording

13. As the owner, I want a quick-log form with exactly two required fields, so that recording never costs more than a few seconds.
14. As the owner, I want to record multiple logs against the same project on the same day, so that a morning and an evening session both count.
15. As the owner, I want to attach an optional duration, so that effort is visible when I care and invisible when I do not.
16. As the owner, I want to attach optional tags to a log, so that I can mark a session without maintaining a taxonomy.
17. As the owner, I want to attach up to four images to a log, so that a screenshot or a photo can stand as evidence.
18. As the owner, I want to edit a log's text, duration, tags and images afterwards, so that a hurried entry can be cleaned up.
19. As the owner, I cannot move a log to a different day or project, so that the record of when something happened stays trustworthy.
20. As the owner, I want a single screen that answers "did I record today", per project, so that one glance settles it.

### Business days

21. As the owner, I want a day to run from 04:00 to 04:00 local time, so that something written at 02:00 still belongs to yesterday.
22. As the owner, I want that boundary to hold across daylight-saving changes, so that streaks do not jump twice a year.
23. As the owner, I want the business day computed on the server, so that a phone in another timezone cannot rewrite my history.
24. As the owner, I want the system to reject a date in the future or in the distant past, so that the record cannot be fabricated wholesale.

### Streaks

25. As the owner, I want a project's streak to count consecutive expected days that were recorded, so that persistence has a number.
26. As the owner, I want a rest day to be skipped rather than counted or broken, so that a weekend does not punish me.
27. As the owner, I want today's absence not to break the chain before the day is over, so that the afternoon is not treated as a failure.
28. As the owner, I want a missed expected day to reset the streak to zero, so that the number stays honest.
29. As the owner, I want my all-time longest streak preserved forever, so that past discipline is not erased by a bad month.
30. As the owner, I want each project's streak computed independently, so that one lapse does not contaminate the others.
31. As the owner, I want to see a flame with the longest active streak once it reaches seven days, so that a good run is visibly acknowledged.

### Rest days

32. As the owner, I want a global default of Saturday and Sunday as rest days, so that weekends are sane out of the box.
33. As the owner, I want to change which weekdays are rest days, so that my actual schedule is reflected.
34. As the owner, I want a project to override the global rest days, so that one project can run on different days.
35. As the owner, I want changing rest days to leave history untouched, so that editing a setting cannot retroactively break a streak.

### Pause, finish, archive

36. As the owner, I want to pause a project while travelling, so that absence is declared rather than counted as failure.
37. As the owner, I want the streak to freeze while paused, so that resuming continues where I stopped.
38. As the owner, I want the pause to take effect the same day I declare it, so that it works when I remember at the airport.
39. As the owner, I want to finish a project permanently, so that completing something is a distinct, recorded act.
40. As the owner, I want finishing to require a second confirmation, so that a misclick cannot end a project.
41. As the owner, I want archived projects to be reversible, so that putting something away is not the same as killing it.
42. As the owner, I want finished and archived projects to stop raising alerts, so that the alarm follows what I am actually doing.

### Backfilling

43. As the owner, I want to backfill a day I forgot, within seven days, so that a small lapse can still be recorded accurately.
44. As the owner, I want backfilled logs to be marked as such, so that later I can tell what was written at the time.
45. As the owner, I want backfilling not to repair a broken streak, so that the number means what it claims to mean.
46. As the owner, I want backfilling not to raise my longest streak, so that the record cannot be gamed by my future self.
47. As the owner, I want backfills capped at three per day, so that a lost week cannot be manufactured in one sitting.
48. As the owner, I want the server to decide whether something is a backfill, so that a client cannot lie about it.

### Alerts

49. As the owner, I want an email at 21:00 naming the projects I have not recorded today, so that the day can still be saved.
50. As the owner, I want one digest email rather than one per project, so that the alarm stays readable.
51. As the owner, I want the email to include each project's streak and consecutive missed days, so that I understand the cost of continuing to ignore it.
52. As the owner, I want the alert to be sent at most once per day, so that a retry or a restart cannot spam me.
53. As the owner, I want no email on days when everything is recorded, so that silence means success.
54. As the owner, I want no escalating second email for long absences, so that the channel stays credible.
55. As the owner, I want a failed email delivery to be logged and dropped, so that mail problems cannot break the rest of the system.

### Calendar and statistics

56. As the owner, I want a month calendar where each day's shade shows how much of that day was recorded, so that a month is legible in one image.
57. As the owner, I want rest days and paused periods to render neutrally, so that the calendar does not accuse me of days that were never mine.
58. As the owner, I want to tap a day and see its logs, so that the calendar is also the way back to the detail.
59. As the owner, I want a completion rate and a clean completion rate per project, so that I can distinguish "caught up later" from "actually did it".
60. As the owner, I want both rates to show a dash rather than 0% when there is no expectation yet, so that a new project is not scored before it starts.
61. As the owner, I want a twelve-week rollup and a thirty-day log count, so that I can see direction without reading every day.
62. As the owner, I want a project page with its streak history, rates and schedule rule, so that one project can be examined properly.

### Settings, export, deletion

63. As the owner, I want to change my email and password, so that the account stays under my control.
64. As the owner, I want to export everything as a single JSON file, so that my data is never trapped.
65. As the owner, I want a deleted project to be restorable for thirty days, so that an accident is recoverable.
66. As the owner, I want deletion to be genuinely final after thirty days, so that "deleted" means deleted.
67. As the owner, I want the storage of my logs and images to be private to my session, so that a public URL cannot leak a diary.
68. As the owner, I want the whole site behind HTTPS with sane security headers, so that a coffee-shop network is not a hazard.

## Implementation Decisions

### Scope and constraints

- The deliverable is the Phase 1 web application: everything a single person needs to run this daily on a phone. The React Native client is Phase 2 and is not built here.
- Three decisions are already locked and bind this spec: a check-in **is** a log (no separate check-in entity), PostgreSQL 16 is the store, and a business day runs 04:00–04:00 Europe/Madrid. See ADR 0001, 0002, 0003.

### Domain kernel

Two modules carry all the temporal reasoning, and nothing else is allowed to duplicate them:

- **Business-day module** — converts an instant to a business day, converts a business day to its UTC bounds, resolves the rest-day set in effect for a project on a given day, and enumerates expected days over a range. The window is capped at 400 days and reports truncation rather than silently shortening.
- **Streak module** — the single implementation of streak counting. It is a pure function over an ordered list of expected days and a set of recorded days, plus the anchor rule in R5.

Both take the current instant as an argument rather than reading the clock, which is what makes them testable without freezing system time.

### Persistence

Nine tables, singular snake_case names: `account`, `project`, `project_status_change`, `schedule_rule`, `log`, `log_tag`, `attachment`, `alert_log`, `session`.

Decision-rich details worth fixing now:

- `account` is a single row, created from configuration at first boot; there is no registration path.
- `schedule_rule` carries `effective_from` and allows a null `project_id` for the global default, with `UNIQUE NULLS NOT DISTINCT (project_id, effective_from)`. Rest days are therefore versioned, which is how R14 (no retroactive rewrite) is enforced structurally rather than by discipline.
- `project.status` is a denormalised copy of the newest `project_status_change`; both are written in the same transaction.
- `log` has no unique constraint on `(project_id, business_date)` — several logs per day are legal. It carries a nullable unique `client_id` reserved for Phase 2 idempotent replay.
- `log.backfilled` is derived server-side from `business_date < current business day` and is never accepted from a client.
- `alert_log.business_date` is unique. A row is written even when nothing is sent (outcome `skipped`), so the health endpoint can distinguish "nothing to report" from "the scheduler is dead".
- Soft deletes use `deleted_at`; a daily cleanup job hard-deletes rows and files thirty days after deletion.

### API contracts

All endpoints live under `/api`. Errors share one shape: `{"error": {"code", "message", "details"}}` with a stable machine-readable `code`.

Authentication: login, logout, and current-account lookup, all session-cookie based.

Reading and writing: today's cards; project list, create, detail, update, status transition, schedule update, delete and restore; log list, create, update and delete; attachment upload and delete; calendar by month; statistics; full export; health.

Two contract decisions matter more than the rest:

- Log update refuses to change `business_date` or `project_id`. Changing when something happened is expressed as delete plus backfill, which keeps the seven-day window and the three-per-day cap unbypassable.
- Project status transitions and schedule changes are appended, never patched in place, so both carry an effective date and neither can rewrite history.

### Alerting

A single in-process scheduled job runs at 21:00 local. It writes its intent to `alert_log` first using an insert-that-may-conflict, and only the winner of that insert proceeds to compose and send. Delivery is one digest email through an SMTP port that the application owns; the port is injected, so tests observe the outbound message without a live server. Failures retry a bounded number of times and then record a failed outcome without propagating.

### Files

Uploads are accepted only for images, verified by decoding rather than by trusting the declared type, capped at 5 MB and four per log, stored under a date-partitioned path with a random identifier, and served through the authenticated proxying path rather than by direct filesystem exposure.

### Web client

Next.js App Router with server-side rendering for first paint and TanStack Query for all server state; zustand is limited to interface state. The client performs no date arithmetic that affects behaviour: it formats what the API returns. Because the browser talks to one origin and the server-renderer talks to an internal host, the client must resolve two base URLs and forward the session cookie on the server side.

Visual design is **not** decided in this document. [`docs/specs/0002-web-interface-design.md`](0002-web-interface-design.md) owns it, and [`docs/interface-preview.html`](../interface-preview.html) is its normative rendering: every screen must reproduce that preview's structure, copy, tokens, components and rhythm. A screen that "works but looks different" is not done. No icon package, component library or webfont may be added without an ADR, because each would break that constraint by construction.

### Deployment

Docker Compose on an Ubuntu host behind nginx: proxy, web, api, database, and an opt-in backup profile. Only the proxy is exposed. The API runs a single worker because the scheduler is in-process and must not be duplicated.

## Testing Decisions

**What makes a good test here.** Tests assert observable behaviour: given a recorded history and a stated "now", the API returns these numbers, this calendar, this alert decision. They do not assert how the computation is structured, which queries ran, or which internal function was called. A test that breaks when the streak implementation is refactored without changing results is a bad test. The one exception is the date kernel, where the unit of behaviour *is* the pure function.

**Two seams, as agreed.**

1. **HTTP API (primary, highest).** Drive the running application through an ASGI client with a fabricated clock and a fake mail sender. This is where every rule gets its end-to-end verification: creating projects, recording logs, backfilling, transitioning status, and reading today's cards, calendar and statistics. Session cookies are exercised for real, so auth is covered by the same seam.
2. **Date kernel (secondary, pure).** The business-day and streak functions are tested directly with table-driven cases. This exists because the risky behaviour is combinatorial in dates — month ends, daylight-saving days, rest-day boundaries, pause spans — and driving thirty such cases through HTTP would add indirection without adding confidence.

No third seam. Persistence correctness (uniqueness, checks, soft-delete filtering) is asserted through the API seam, not through a separate database-test layer.

**Clock and mail are not seams.** They are injection points inside the harness: `now` is supplied explicitly, and mail delivery is a port with a fake implementation. Tests never depend on wall-clock time or a network mailbox.

**What the tests must cover before the slice counts as done:** all fourteen edge cases enumerated in the PRD, plus the alert job's idempotency under a repeated run, plus session expiry and throttling. Streak tests specifically must include a rest day inside a run, a paused span inside a run, a backfilled day that must not extend the streak, and both daylight-saving days.

**Prior art.** There is none: this is the first code in the repository, so these tests establish the pattern every later slice follows. The convention they should set is: name the test after the rule it protects (citing the rule identifier), build the smallest history that exposes the boundary, and assert on the response body rather than on internals.

## Out of Scope

- The React Native client and its offline queue, including `client_id` replay (the column exists; nothing uses it).
- Charts, trend lines, weekly reports and any generated summary. The statistics endpoint returns four numbers and that is the ceiling for now.
- Any third-party synchronisation: calendar, GitHub, health, or otherwise.
- Multiple users, sharing, teams, invitations, or tenancy of any kind.
- Push notifications, desktop notifications, or anything beyond email.
- Internationalisation and configurable timezones; both are deliberately fixed.
- Rich text, markup, backlinks, or any note-taking affordance in the log body.
- Import from other tools. Export exists; import does not.
- Backup automation is operational work specified separately; the application only has to be restorable, not self-backing-up.

## Further Notes

- **Three external dependencies must be provisioned before the first real deployment:** an SMTP credential for the alert email, object storage credentials for offsite backups, and a domain with a certificate. None of them block development, because mail is a port and backups are a profile.
- **The alert path is the system's only fragile external dependency.** It is deliberately kept out of the authentication path — logging in must never depend on SMTP — and its failure is recorded rather than raised.
- **Two settings are fixed on purpose** and should not be made configurable as a convenience: the 04:00 boundary and the 21:00 alert hour. The first is load-bearing for every historical streak; the second is load-bearing for habit. Both should be revisited only with an ADR.
- **The acceptance bar for this phase is behavioural, not technical:** fourteen consecutive days of genuine personal use with no streak error found by spot-checking three random projects. If the owner stops using it before day fourteen, the spec is wrong regardless of test coverage.
