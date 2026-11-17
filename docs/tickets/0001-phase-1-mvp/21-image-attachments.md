# 21: Image attachments

**What to build:** A log can carry visual evidence — a screenshot or a photograph — stored privately and served only to the owner's session.

**Blocked by:** 07

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] Up to four images can be attached to a log, each no larger than 5 MB.
- [ ] Only JPEG, PNG and WebP are accepted, and the type is decided by decoding the bytes, not by trusting the declared content type or the filename extension.
- [ ] An image is served only to an authenticated session; requesting its URL without a session returns 401.
- [ ] Stored filenames are random; the original filename never appears on disk or in a URL.
- [ ] An attached image is visible on the log in the day view and in the project timeline.
