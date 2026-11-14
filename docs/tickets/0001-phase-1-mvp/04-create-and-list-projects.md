# 04: Create and list projects

**What to build:** The owner can create a project with a name and a start date, and see it immediately in the project list and on today's cards as not yet recorded.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Creating a project needs only a name and a start date; the start date defaults to today's business day.
- [ ] The new project appears in the list under Active and on today's view as not recorded, without a manual refresh.
- [ ] An empty name, or one longer than 60 characters, is rejected with 422 and a stable machine-readable code.
- [ ] The list persists its ordering across reloads.
- [ ] A project can be created with a start date in the past, and doing so does not immediately produce a backlog of misses.
- [ ] Creating a project with a start date in the future leaves it out of today's view until that day arrives.
