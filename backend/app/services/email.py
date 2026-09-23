"""Transactional email abstraction. Configure NIPAM_EMAIL_PROVIDER=smtp to send
through any SMTP-compatible transactional provider (e.g. SES, Postmark, Mailgun)."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from ..config import get_settings

log = logging.getLogger("nipam.email")
outbox: list[dict] = []  # captured messages for the console provider (dev/tests)


def send_email(to: str, subject: str, text: str) -> None:
    s = get_settings()
    if s.email_provider == "smtp":
        msg = EmailMessage()
        msg["From"] = s.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text)
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if s.smtp_user:
                smtp.login(s.smtp_user, s.smtp_password)
            smtp.send_message(msg)
        return
    outbox.append({"to": to, "subject": subject, "text": text})
    del outbox[:-200]
    log.info("[console email] to=%s subject=%s", to, subject)
