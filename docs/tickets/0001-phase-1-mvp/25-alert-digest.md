# 25: Alert digest

**What to build:** The email that makes the system impossible to ignore — one message naming the projects that were expected today and were not recorded, with the cost of continuing to ignore them.

**Blocked by:** 11, 18

**Status:** ready-for-agent

- [ ] Triggering the digest sends exactly one email listing every active project whose current business day is an expected day with no log.
- [ ] Each entry carries the project name, its current streak, its consecutive missed days, and a direct link into the application.
- [ ] When nothing was missed, no email is sent at all.
- [ ] A mail server failure is recorded and does not propagate to the caller or block anything else.
- [ ] Paused, finished and archived projects never appear in the digest.
- [ ] Mail delivery goes through an injected port, so the outbound message is observable in tests without a live server.
