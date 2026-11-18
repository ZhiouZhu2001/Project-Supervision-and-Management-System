# 06: Business day

**What to build:** "Today" is defined once, on the server, as a business day running 04:00 to 04:00 Europe/Madrid — and the interface always shows which business day the owner is currently in, so a session at 02:00 visibly belongs to yesterday.

**Blocked by:** 05

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** done

- [ ] The current business day is shown somewhere always visible in the interface.
- [ ] With the clock at 03:59 local the displayed day is the previous calendar date; at 04:01 it is the current one.
- [ ] The current business day is exposed by the API, and the client never computes it.
- [ ] On both daylight-saving switch days the business day advances by exactly one, despite one being 23 hours and the other 25.
- [ ] A request that supplies a business date in the future is rejected, using the same validation as log creation will use.
