"""Outbound mail behind a port.

The port exists so tests can observe what would have been sent without a live
server, and so production can swap SMTP for anything else later without
touching the digest logic.
"""

import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Protocol

from app.config import get_settings


class Mailer(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None: ...


@dataclass
class SentMessage:
    to: str
    subject: str
    body: str


@dataclass
class RecordingMailer:
    """Keeps everything it was asked to send. Used by tests and by dry runs."""

    sent: list[SentMessage] = field(default_factory=list)

    def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append(SentMessage(to=to, subject=subject, body=body))


class DisabledMailer:
    """No SMTP configured: say so loudly, but do not break the caller."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        raise RuntimeError("SMTP is not configured (set SMTP_HOST)")


@dataclass
class SmtpMailer:
    host: str
    port: int
    sender: str
    username: str | None = None
    password: str | None = None
    use_starttls: bool = True
    timeout: int = 15

    def send(self, *, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as client:
            if self.use_starttls:
                client.starttls()
            if self.username and self.password:
                client.login(self.username, self.password)
            client.send_message(message)


def build_mailer() -> Mailer:
    settings = get_settings()
    if not settings.smtp_host:
        return DisabledMailer()
    return SmtpMailer(
        host=settings.smtp_host,
        port=settings.smtp_port,
        sender=settings.smtp_from or settings.alert_email,
        username=settings.smtp_username or None,
        password=settings.smtp_password or None,
        use_starttls=settings.smtp_starttls,
    )
