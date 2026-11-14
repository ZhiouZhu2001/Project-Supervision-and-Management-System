# 12: Edit a log

**What to build:** A hurried entry can be cleaned up afterwards — text, duration and tags — without the record of *when* or *what* becoming editable.

**Blocked by:** 07

**Status:** ready-for-agent

- [ ] Body, duration and tags can be edited, and the change is reflected in the day's list, the calendar and the statistics.
- [ ] Editing cannot change the business date or the project; an attempt returns 422.
- [ ] The same body and duration validation as creation applies, with the same error codes.
- [ ] Editing a log never changes whether that day counts as checked in.
- [ ] An edited log keeps its position in the day's timeline rather than jumping to the end.
