# 11: Per-project rest override

**What to build:** A single project can run on a different weekly schedule from the rest. The override is versioned by effective date, so changing it today cannot rewrite last month's streak.

**Blocked by:** 10

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] A project without an override inherits the global rest weekdays.
- [ ] An override replaces the global set for that project only, from its effective date onward.
- [ ] Recording an override for a date that already has one is rejected with 422 rather than silently replacing it.
- [ ] A history fixture with a rule change mid-stream keeps every earlier streak and rate byte-identical after the change.
- [ ] The project detail page shows which rule is in effect today and when it started.
