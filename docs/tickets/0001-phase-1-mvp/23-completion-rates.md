# 23: Completion rates

**What to build:** Two numbers per project that answer different questions — how much of what was expected got recorded, and how much of it was recorded at the time rather than patched in afterwards.

**Blocked by:** 17, 18, 11

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** done

- [ ] The completion rate counts backfilled days as recorded; the clean completion rate does not.
- [ ] Both rates show a dash, not 0% or 100%, when a project has no expected days yet.
- [ ] Paused days and rest days appear in the denominator of neither rate.
- [ ] Rates match a hand-computed fixture covering rest days, a pause, one backfill and one genuine miss.
- [ ] Rates are returned by the API only; the client performs no rate arithmetic.
