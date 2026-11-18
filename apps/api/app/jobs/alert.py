"""Run the digest once, by hand.

The scheduler does this on its own at 21:00; this entry point exists so the
job can be proven, re-run after a fix, and observed in production without
waiting for the evening.
"""

import asyncio
import json
from dataclasses import asdict

from app.config import get_settings
from app.db import get_session_factory
from app.services.alerts import run_digest
from app.services.business_day import today_business_date
from app.services.mail import build_mailer


async def _main() -> None:
    settings = get_settings()
    async with get_session_factory()() as session:
        report = await run_digest(
            session,
            build_mailer(),
            to=settings.alert_email or settings.app_email,
            current=today_business_date(),
            base_url=settings.app_base_url,
        )
    print(json.dumps(asdict(report), default=str))


if __name__ == "__main__":
    asyncio.run(_main())
