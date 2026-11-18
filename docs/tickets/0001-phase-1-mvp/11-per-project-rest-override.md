# 11: Per-project rest override

**What to build:** A single project can run on a different weekly schedule from the rest. The override is versioned by effective date, so changing it today cannot rewrite last month's streak.

**Blocked by:** 10

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] A project without an override inherits the global rest weekdays.
- [ ] An override replaces the global set for that project only, from its effective date onward.
- [ ] Setting an override twice for the same effective date updates that day's rule rather than failing; nothing earlier is touched. (Changed from "reject duplicates" during implementation: a same-day correction is a real action, and refusing it made the screen unusable.)
- [ ] Clearing an override returns the project to the account default.
- [ ] A history fixture with a rule change mid-stream keeps every earlier streak and rate byte-identical after the change.
- [ ] The project detail page shows which rule is in effect today and when it started.
