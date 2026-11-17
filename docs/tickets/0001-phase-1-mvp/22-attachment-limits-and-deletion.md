# 22: Attachment limits and deletion

**What to build:** The edge of the attachment feature — what happens when someone tries too much, and what happens when an image is no longer wanted.

**Blocked by:** 21

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** ready-for-agent

- [ ] A fifth image on one log is rejected with 422, and the four existing images remain intact.
- [ ] An image above the size limit is rejected with 422, and the request body limit at the proxy rejects oversized uploads before they reach the application.
- [ ] Deleting an image removes both the stored file and its metadata row.
- [ ] Deleting or purging a log removes all of its images, leaving no orphaned files on disk.
- [ ] Storage paths are partitioned by month and collision-free under concurrent uploads.
