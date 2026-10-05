"""WhatsApp abstraction, mirroring ``sms``.

NIPAM_WHATSAPP_PROVIDER=cloud sends through the Meta WhatsApp Business Cloud
API. WhatsApp only allows a business to start a conversation with an approved
message template, so create a template (default name ``nipam_update``) whose
body contains one ``{{1}}`` variable, e.g. "NIPAM update: {{1}}", and set
NIPAM_WHATSAPP_TOKEN and NIPAM_WHATSAPP_PHONE_NUMBER_ID. Members receive
WhatsApp messages only if they switched the channel on and verified their phone.
"""

from __future__ import annotations

import logging

import httpx

from ..config import get_settings

log = logging.getLogger("nipam.whatsapp")
outbox: list[dict] = []


class WhatsAppProvider:
    def send(self, to: str, text: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleWhatsAppProvider(WhatsAppProvider):
    def send(self, to: str, text: str) -> None:
        outbox.append({"to": to, "text": text})
        del outbox[:-200]
        log.info("[console whatsapp] to=%s", to)


class CloudWhatsAppProvider(WhatsAppProvider):
    def send(self, to: str, text: str) -> None:
        s = get_settings()
        httpx.post(
            f"https://graph.facebook.com/{s.whatsapp_api_version}/{s.whatsapp_phone_number_id}/messages",
            json={
                "messaging_product": "whatsapp",
                "to": to.lstrip("+"),
                "type": "template",
                "template": {
                    "name": s.whatsapp_template,
                    "language": {"code": s.whatsapp_template_language},
                    "components": [{"type": "body", "parameters": [{"type": "text", "text": text}]}],
                },
            },
            headers={"Authorization": f"Bearer {s.whatsapp_token}"},
            timeout=15,
        ).raise_for_status()


def get_whatsapp_provider() -> WhatsAppProvider | None:
    s = get_settings()
    if s.whatsapp_provider == "console":
        return ConsoleWhatsAppProvider()
    if s.whatsapp_provider == "cloud":
        return CloudWhatsAppProvider()
    return None


def send_whatsapp(to: str, text: str) -> bool:
    provider = get_whatsapp_provider()
    if not provider:
        return False
    try:
        provider.send(to, text)
    except httpx.HTTPError:
        log.exception("WhatsApp delivery to %s failed", to)
        return False
    return True
