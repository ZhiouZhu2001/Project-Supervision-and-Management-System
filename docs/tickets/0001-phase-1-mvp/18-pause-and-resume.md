# 18: Pause and resume

**What to build:** Absence can be declared instead of counted. A paused project stops demanding records, and its streak freezes exactly where it was so that resuming continues rather than restarts.

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] A pause takes effect on the business day it is declared, not the following day.
- [ ] Paused days are not expected days: no red state, no alert candidate, and excluded from completion-rate denominators.
- [ ] A streak of N before the pause is still N immediately after resuming, regardless of how long the pause lasted.
- [ ] The resume day is an expected day again.
- [ ] Every status change is appended with its effective date rather than overwriting the previous value.
