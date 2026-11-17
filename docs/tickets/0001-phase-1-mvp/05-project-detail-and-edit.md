# 05: Project detail and edit

**What to build:** Each project has a detail page, and from there the owner can rename it, recolour it and reorder it — changes visible immediately in the list and on today's view.

**Blocked by:** 04

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] The detail page shows name, start date, status, colour and note, plus that project's logs (none yet).
- [ ] The streak is not shown here yet; it arrives with ticket 08 and must not be faked in the meantime.
- [ ] Renaming updates the list and the detail page without a full page reload.
- [ ] Colour and sort order persist and reorder the list.
- [ ] Editing cannot change the start date or the status; those are separate operations and an attempt returns 422.
- [ ] A rename to an empty string is rejected with the same code as creation.
