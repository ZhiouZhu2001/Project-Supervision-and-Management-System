# 20: Archive and unarchive

**What to build:** A project can be put away without being finished — reversible, silent, and excluded from every count until it is brought back.

**Blocked by:** 18

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** done

- [ ] Archiving is reversible; unarchiving returns the project to active.
- [ ] An archived project appears in no active list, is excluded from statistics, and is never an alert candidate.
- [ ] Unarchiving restores the project's data and streak exactly as they were at archive time.
- [ ] Archiving is offered for paused and active projects only; a finished project cannot be archived.
- [ ] Archiving does not delete or modify any log.
