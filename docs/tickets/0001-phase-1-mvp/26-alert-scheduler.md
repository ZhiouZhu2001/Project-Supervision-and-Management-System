# 26: Alert scheduler

**What to build:** The digest fires by itself at 21:00 local, exactly once per business day, whether or not anyone is watching — and the system can prove afterwards that it ran.

**Blocked by:** 25

**Status:** ready-for-agent

- [ ] The alert fires automatically at 21:00 Europe/Madrid, computed from the business-day module rather than from a fixed server timezone.
- [ ] Running the job twice for the same business day sends one email, not two.
- [ ] A row recording the decision is written even when nothing is sent, so a quiet day and a dead scheduler are distinguishable.
- [ ] The health endpoint reports the last business day the job judged; a stale value is visible as a defect.
- [ ] The job runs in a single process — a second worker must not mean a second email.
- [ ] A restart of the application across 21:00 does not lose that day's alert.
