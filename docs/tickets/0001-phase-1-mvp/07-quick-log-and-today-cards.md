# 07: Quick log and today cards

**What to build:** The core interaction. Pick a project, type one line, save — and that project's card on today's view flips to recorded. This is the first moment the product does the thing it exists to do.

**Blocked by:** 06

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** done

- [ ] The quick-log form requires exactly two fields: a project and a body. Nothing else is required.
- [ ] Saving a log flips that project's card to recorded without a full page reload.
- [ ] Duration is optional and accepts 0–1440 minutes; anything outside that range is rejected with 422.
- [ ] A body that is empty, or longer than 2000 characters, is rejected with 422.
- [ ] A future business date is rejected, and so is a date earlier than the project's counting start (`max(start date, creation business day)`).
- [ ] Two logs for the same project on the same business day both save, and both are visible on the day's list.
- [ ] The whole path — open the app, pick a project, type a line, save — is demonstrated to complete in ten seconds or less on a phone-sized viewport.
