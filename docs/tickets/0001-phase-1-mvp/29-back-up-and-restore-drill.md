# 29: Back up and restore drill

**What to build:** The guarantee that a bad night does not cost the diary — an encrypted backup that leaves the machine, and a restore that has actually been performed once rather than assumed to work.

**Blocked by:** 28

**Status:** ready-for-agent

- [ ] A nightly job dumps the database and increments the image store, encrypts both, and uploads them off the machine.
- [ ] Retention keeps seven daily, four weekly and twelve monthly snapshots, and prunes older ones automatically.
- [ ] A restore into a clean stack reproduces the data and the test suite passes against the restored database.
- [ ] The drill is performed, and its date, duration and any surprises are written down next to the backup procedure.
- [ ] A backup failure is surfaced — a silent backup job is treated as a broken one.
