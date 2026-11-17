# 24: Rollup and counts

**What to build:** Direction, not detail — a twelve-week rollup and a thirty-day log count alongside the per-project rates, on one page.

**Blocked by:** 23

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] A twelve-week rollup reports recorded against expected for each of the last twelve weeks.
- [ ] A thirty-day log count reports how many logs were written in the last thirty business days.
- [ ] The statistics page presents all four metrics without a per-project round trip, and renders within 300 ms locally.
- [ ] Every figure on the page agrees with the calendar for the same period.
- [ ] Weeks with no expectation are omitted rather than plotted as zero.
