# 08: Streak on cards

**What to build:** Each project's card shows its current streak, derived from recorded days, so that persistence becomes a number the owner can watch move.

**Blocked by:** 07

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] A project recorded yesterday and today shows a streak of 2; recorded only today it shows 1.
- [ ] Missing an expected day resets the streak, and the next recorded expected day starts again at 1.
- [ ] Not having recorded today does not reduce the streak while the day is still running.
- [ ] Streaks are computed independently per project; a lapse in one leaves the others untouched.
- [ ] Streak values reported by the API match the pure kernel for the same fixture histories.
- [ ] Streak computation is a single implementation — no SQL, client or script recomputes it.
