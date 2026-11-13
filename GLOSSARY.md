# Project Supervision and Management System

A one-person self-supervision tool that turns "what did I actually do today" into a queryable fact, and that wakes you up with a red status and an email on the days you record nothing. Every term below is normative: code identifiers, API names, UI copy and comments use these words.

## Actors

**Owner** (`account`):
The single person who uses this system — you. No registration, no second account, no admin/regular-user split.
_Avoid_: user, member, customer, tenant

## Records

**Project** (`project`):
A thing you intend to keep doing, with a start date and its own independent streak. A project is a dimension that logs are filed under, not a task list.
_Avoid_: task, goal, card, ticket, board

**Log** (`log`):
One written entry for one project on one business day, with a body and optional duration, tags and images. Logs are the only positive fact in the system.
_Avoid_: entry, note, journal, post, check-in record

**Business day** (`business_day`):
A 24-hour cycle bounded at 04:00 Europe/Madrid local time. Something written at 02:00 belongs to "yesterday".
_Avoid_: calendar day, date, day

**Check-in** (`check_in`):
The fact that a project has at least one log on a business day. A check-in is not an action and not a table — it is inferred from logs.
_Avoid_: punch, clock-in, checkin, attendance

**Expected day** (`expected_day`):
A business day on which a project *ought* to be logged. Determined by rule R3; it excludes rest days, paused periods, and any date before the project started counting.

**Rest day** (`rest_day`):
A weekday on which logging is not required. A rest day neither counts toward a streak nor breaks one.
_Avoid_: holiday, day off, skip day, weekend

**Miss** (`miss`):
An expected day that ended without a log. A miss is computed, never stored, and never becomes a "negative record".
_Avoid_: failure, gap, debt, missed check-in

**Backfill** (`backfill`):
Writing a log for a past business day. A backfill carries a `backfilled` marker and **does not repair** the streak.
_Avoid_: backdate, retro-entry, correction

## Continuity and evaluation

**Streak** (`streak`):
Counting back from the most recent expected day, the number of consecutive expected days that were checked in without a miss, rest day or pause breaking the chain. Computed per project.
_Avoid_: chain, run, consecutive days, win streak

**Break** (`break`):
A miss on an expected day, resetting that project's streak to zero. The all-time best is retained forever.
_Avoid_: reset, failure, lapse

**Longest streak** (`longest_streak`):
The highest streak a project has ever reached. It never decreases, and backfilling does not increase it.

**Flame** (`flame`):
Shown next to the avatar as 🔥 with a number when the largest current streak across all active projects reaches 7.
_Avoid_: badge, level, trophy

**Completion rate** (`completion_rate`):
Checked-in expected days divided by all expected days. Backfilled days count as checked in.

**Clean completion rate** (`clean_completion_rate`):
Completion rate excluding backfilled days. It measures whether you actually did it at the time, not whether you later patched the record.

## Lifecycle

**Active** (`active`):
The normal state: participates in alerts, streaks and statistics.

**Paused** (`paused`):
Temporarily halted (travel, illness). No alerts, no logging required, the streak freezes in place and resumes unchanged.

**Finished** (`finished`):
The project reached its goal and was closed properly. The final and longest streaks are preserved, it leaves alerts and active statistics, and it moves to the completed list. This transition is **not reversible**.

**Archived** (`archived`):
The project was put away — neither finished nor wanted in view. Read-only, excluded from every statistic, no alerts, and reversible at any time.

> The difference between **finished** and **archived** is intent, not data: finishing is a wrap-up worth showing, archiving is quiet storage. Only a user can declare a project finished; the system never infers it.

**Schedule rule** (`schedule`):
Which weekdays count as rest days for a project. Rules carry an effective date and apply only from that date onward — they never rewrite history.
_Avoid_: settings, config, cadence, frequency
