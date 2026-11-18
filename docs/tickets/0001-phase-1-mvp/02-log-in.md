# 02: Log in

**What to build:** The owner can sign in with an email and password and reach the application; anyone without a session sees the login page instead. There is exactly one account, created from configuration on first boot, and no way to register a second one.

**Blocked by:** 01

**Visuals:** every screen this ticket touches must match [`docs/interface-preview.html`](../../interface-preview.html) — see [spec 0002](../../specs/0002-web-interface-design.md). Structure, copy, tokens and components are normative; "works but looks different" is not done.

**Status:** done

- [ ] First boot creates exactly one account from configuration; no registration route exists in the application.
- [ ] Correct credentials set a session cookie that is HttpOnly and Secure in production, and the owner lands on the application shell.
- [ ] Visiting any application route without a session redirects to the login page.
- [ ] Any API call without a session returns 401 using the standard error shape.
- [ ] Logout deletes the session server-side; replaying the old cookie is rejected.
- [ ] The password is stored only as a memory-hard hash, and the plaintext never appears in a log line or an error body.
