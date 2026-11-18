"""How long a deleted thing stays recoverable.

One number, used by logs, projects and the cleanup job, because "thirty days"
that differs per entity is a bug waiting to be written.
"""

from datetime import timedelta

RETENTION = timedelta(days=30)
