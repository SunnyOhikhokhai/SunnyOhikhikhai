"""Fan-out of in-app, email and SMS notifications, respecting each member's
preferences. Account/security messages are essential and bypass preferences."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import MemberAreaCouncil, Notification, NotificationPreference, User
from .email import send_email
from .sms import send_sms

PREF_FIELDS = {
    "announcement": ("in_app_announcements", "email_announcements", "sms_announcements"),
    "event": ("in_app_events", "email_events", "sms_events"),
    "community": ("in_app_community", "email_community", None),
    "council_update": ("in_app_council_updates", None, None),
    "account": (None, None, None),
}


@dataclass
class Outbound:
    emails: list[tuple[str, str, str]] = field(default_factory=list)
    sms: list[tuple[str, str]] = field(default_factory=list)

    def schedule(self, tasks: BackgroundTasks | None) -> None:
        for to, subject, text in self.emails:
            if tasks:
                tasks.add_task(send_email, to, subject, text)
            else:
                send_email(to, subject, text)
        for to, text in self.sms:
            if tasks:
                tasks.add_task(send_sms, to, text)
            else:
                send_sms(to, text)


def _wants(prefs: NotificationPreference | None, attr: str | None) -> bool:
    if attr is None:
        return False
    return bool(prefs and getattr(prefs, attr))


def notify_users(
    db: Session,
    users: list[User],
    ntype: str,
    title: str,
    body: str = "",
    link: str | None = None,
    tasks: BackgroundTasks | None = None,
) -> int:
    in_app_attr, email_attr, sms_attr = PREF_FIELDS[ntype]
    out = Outbound()
    count = 0
    for u in users:
        prefs = u.preferences
        if ntype == "account" or (in_app_attr and (prefs is None or getattr(prefs, in_app_attr))):
            db.add(Notification(user_id=u.id, type=ntype, title=title, body=body, link=link))
            count += 1
        if _wants(prefs, email_attr) and u.email_verified_at:
            out.emails.append((u.email, f"NIPAM: {title}", f"{body}\n\nManage your notification preferences in your NIPAM account settings."))
        if _wants(prefs, sms_attr) and u.phone and u.phone_verified_at:
            out.sms.append((u.phone, f"NIPAM: {title}"[:300]))
    db.commit()
    out.schedule(tasks)
    return count


def audience(db: Session, area_council_id: int | None = None) -> list[User]:
    stmt = (
        select(User)
        .options(selectinload(User.preferences))
        .where(User.deleted_at.is_(None), User.status == "active")
    )
    if area_council_id:
        stmt = stmt.join(MemberAreaCouncil, MemberAreaCouncil.user_id == User.id).where(
            MemberAreaCouncil.area_council_id == area_council_id
        )
    return list(db.scalars(stmt).all())
