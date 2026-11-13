# A check-in is a log; there is no separate check-in entity

"Check-in" is not a table — it is the fact that a project has at least one log on a business day. We considered a standalone `check_in` entity (a button pressed once a day) and a hybrid (press the button, then optionally write a log), and rejected both: an independent check-in action reliably produces hollow records that claim a day was worked when nothing was written, which is precisely the self-deception this system exists to prevent. It also adds one mandatory interaction per day, colliding with the "open to saved in under 10 seconds" constraint. A miss is likewise computed at query time rather than stored as a negative record, so there are no negative rows to edit, undo or collide with real ones.

**Options considered**: a dedicated `check_in` table (check-in independent of logs); a hybrid mode that auto-creates a check-in when a log exists. Both were rejected in prototyping against the "hollow check-in" failure case.

**Consequences**: every "did I check in today?" decision must go through the existence of `log` rows, so soft-delete semantics on `log` become load-bearing — deleting the last log of a day genuinely makes that day un-checked-in. That is intentional.
