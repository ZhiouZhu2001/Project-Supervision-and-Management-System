# 17: Backfill

**What to build:** A day that was forgotten can still be recorded within the last week — honestly marked as written later, and explicitly unable to repair the streak it broke.

**Blocked by:** 11

**Status:** ready-for-agent

- [ ] A past business day can be recorded within seven days; a date eight or more days old is rejected with 422.
- [ ] At most three backfilled logs are accepted per project per business day; a fourth is rejected with 422.
- [ ] The server marks a log as backfilled whenever its date precedes the current business day; a client-supplied flag is ignored.
- [ ] Backfilling changes neither the current streak nor the longest streak.
- [ ] The interface states how many backfills remain for the selected day before saving.
- [ ] A backfilled day is visually distinguishable from a day recorded on the day itself.
