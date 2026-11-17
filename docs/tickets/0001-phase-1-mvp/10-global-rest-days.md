# 10: Global rest days

**What to build:** The owner can declare which weekdays are rest days. A rest day requires no record, breaks no streak, and raises no red state — so a weekend stops being a failure.

**Blocked by:** 09

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] Settings expose the global rest weekdays, defaulting to Saturday and Sunday.
- [ ] A rest day is not an expected day: no "not recorded" state, no streak contribution, no red styling.
- [ ] A run of recorded weekdays that spans a weekend keeps its streak intact.
- [ ] Changing the setting does not alter any already-computed streak for past days.
- [ ] Selecting all seven weekdays as rest is either prevented or clearly explained, since it would stop streaks entirely.
