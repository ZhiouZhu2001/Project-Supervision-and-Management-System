# 15: Calendar month

**What to build:** A month at a glance, where each day's shade says how much of that day was recorded against what was expected — so a month of drift or discipline is legible in one image.

**Blocked by:** 11

**Status:** ready-for-agent

- [ ] Days are shaded in four buckets by the ratio of recorded to expected projects, from nothing recorded to everything recorded.
- [ ] Rest days, days before a project started, and paused days render neutrally rather than as failures.
- [ ] Future days are visibly inactive.
- [ ] A day with zero expected projects renders neutral, never as 0% or as a failure.
- [ ] Switching months is instant, because the grid is aggregated server-side rather than assembled in the browser.
- [ ] The calendar agrees exactly with each project's streak for the same days.
