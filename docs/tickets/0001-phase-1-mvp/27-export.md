# 27: Export

**What to build:** One file containing everything the owner ever wrote, so the data is never trapped in a system he might stop trusting.

**Blocked by:** 17, 20, 11

**Status:** ready-for-agent

- [ ] A single download contains projects, logs, tags, attachment metadata, schedule rules and status history.
- [ ] Attachment metadata includes checksums and stored identifiers but not the file bytes.
- [ ] Exporting an account with no projects produces a valid, well-formed document rather than an error.
- [ ] The export contains no password hashes, session identifiers or other authentication material.
- [ ] Restored-from-export data is sufficient to reconstruct the same streaks in a fresh database.
