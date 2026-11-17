# 09: Flame and longest streak

**What to build:** A project's all-time longest streak is preserved forever, and once the longest current streak across active projects reaches seven days the owner's avatar shows a flame with that number.

**Blocked by:** 08

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] Longest streak never decreases, including after a break.
- [ ] The flame appears at exactly seven days, shows that number, and disappears when the maximum falls below seven.
- [ ] Tapping or hovering the flame names the project it belongs to.
- [ ] With no active projects, or with all streaks below seven, no flame is rendered.
