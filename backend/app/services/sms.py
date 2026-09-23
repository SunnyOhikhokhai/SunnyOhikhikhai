"""SMS abstraction so an approved Nigerian SMS provider can be connected later.

Set NIPAM_SMS_PROVIDER=http with NIPAM_SMS_HTTP_URL / NIPAM_SMS_HTTP_TOKEN to post
JSON {"to", "from", "message"} to a provider gateway, or implement a new
``SmsProvider`` subclass for provider-specific APIs.
"""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings

log = logging.getLogger("nipam.sms")
outbox: list[dict] = []


class SmsProvider:
    def send(self, to: str, message: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    def send(self, to: str, message: str) -> None:
        outbox.append({"to": to, "message": message})
        del outbox[:-200]
        log.info("[console sms] to=%s", to)


class HttpSmsProvider(SmsProvider):
    def send(self, to: str, message: str) -> None:
        s = get_settings()
        httpx.post(
            s.sms_http_url,
            json={"to": to, "from": s.sms_sender_id, "message": message},
            headers={"Authorization": f"Bearer {s.sms_http_token}"},
            timeout=15,
        ).raise_for_status()


def get_sms_provider() -> SmsProvider | None:
    s = get_settings()
    if s.sms_provider == "console":
        return ConsoleSmsProvider()
    if s.sms_provider == "http":
        return HttpSmsProvider()
    return None


def send_sms(to: str, message: str) -> bool:
    provider = get_sms_provider()
    if not provider:
        return False
    provider.send(to, message)
    return True
