# 03: Login throttling

**What to build:** Repeated failed sign-ins stop being answered, so the public login endpoint cannot be used to guess a password.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] Five consecutive failures for the same account from the same source lock further attempts for fifteen minutes.
- [ ] During the lock, even the correct password is rejected — throttling that lets the right answer through is not throttling.
- [ ] A successful login after the lock window clears the counter.
- [ ] The lock cannot be bypassed by changing the case of the email address or padding it with whitespace.
- [ ] The response for a locked account is the same shape as a wrong password, so the endpoint does not confirm which addresses exist.
