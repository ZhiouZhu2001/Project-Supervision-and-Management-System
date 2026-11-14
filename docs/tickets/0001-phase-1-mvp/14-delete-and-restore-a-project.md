# 14: Delete and restore a project

**What to build:** A project and everything under it can be removed, recovered for thirty days, and then genuinely destroyed along with its images.

**Blocked by:** 13

**Status:** ready-for-agent

- [ ] Deleting a project requires a confirmation naming the project, and immediately hides it from the list, today's view, the calendar and the statistics.
- [ ] Restoring within thirty days returns the project with its logs intact and its streak recomputed to exactly the pre-deletion value.
- [ ] After the retention window a cleanup job physically deletes the project, its logs, tags, attachment rows and their files.
- [ ] Deleting a project never deletes or alters another project's data.
- [ ] The cleanup job is safe to run repeatedly and reports how many rows and files it removed.
