# 13: Delete a log

**What to build:** A log can be removed. Because a check-in *is* a log, deleting the only log of a day genuinely makes that day un-checked-in — the calendar and the streak must both agree with that immediately.

**Blocked by:** 12

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] Deleting a log removes it from the day's list and from the calendar.
- [ ] If it was the only log of that business day, the day becomes un-recorded and the streak recomputes accordingly.
- [ ] Deleting today's only log flips that project's card back to the red not-recorded state.
- [ ] A deleted log can be restored within thirty days, with its original date and content.
- [ ] After the retention window the log is gone permanently and restore is refused.
