# 01: Platform skeleton

**What to build:** One command brings up the whole stack — database, API, web client and the single proxy entry point — so that opening the site shows an application shell and the API can prove it can reach the database. Everything after this ticket assumes it exists.

**Blocked by:** None (can start immediately)

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** done

- [ ] `make dev` brings the stack up from a clean checkout in one command, and `make down` stops it cleanly.
- [ ] Opening the site on the host serves the application shell, and every asset comes from the same origin (no cross-origin calls).
- [ ] A health endpoint reports database reachability and the application version, and does not require a session.
- [ ] Database and API ports are bound to loopback only and are unreachable from the host network.
- [ ] After a host reboot every service returns without manual intervention.
- [ ] The database connection is configured for UTC sessions, because all stored timestamps are UTC.
