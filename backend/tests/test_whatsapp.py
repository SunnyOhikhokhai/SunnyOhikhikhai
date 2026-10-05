from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.migrate import untracked_revision
from app.models import User, utcnow
from app.services import whatsapp
from app.services.notify import notify_users


def _enable(monkeypatch):
    monkeypatch.setattr(get_settings(), "whatsapp_provider", "console")


def _set_phone(email: str, verified: bool) -> None:
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == email))
        u.phone = "+2348030000000"
        u.phone_verified_at = utcnow() if verified else None
        db.commit()


def test_whatsapp_is_opt_in_and_needs_verified_phone(member, monkeypatch):
    _enable(monkeypatch)
    prefs = member.get("/api/users/me/preferences").json()["data"]
    assert prefs["whatsapp_enabled"] is True
    assert prefs["whatsapp_announcements"] is False and prefs["whatsapp_events"] is False  # off by default

    email = member.get("/api/auth/me").json()["data"]["user"]["email"]
    _set_phone(email, verified=False)
    r = member.put("/api/users/me/preferences", {"whatsapp_announcements": True})
    assert r.status_code == 422 and r.json()["error"]["code"] == "phone_unverified"
    assert member.put("/api/users/me/preferences", {"whatsapp_events": False}).status_code == 200  # turning off is fine

    _set_phone(email, verified=True)
    r = member.put("/api/users/me/preferences", {"whatsapp_announcements": True})
    assert r.status_code == 200 and r.json()["data"]["whatsapp_announcements"] is True


def test_whatsapp_delivery_respects_preferences(monkeypatch):
    _enable(monkeypatch)
    whatsapp.outbox.clear()
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.email == "member@nipam.local"))
        u.phone = "+2348030000000"
        u.phone_verified_at = utcnow()
        u.preferences.whatsapp_announcements = True
        db.commit()
        notify_users(db, [u], "announcement", "Town hall on Saturday", "Details in the app.")
        notify_users(db, [u], "event", "Event changed")  # events not opted in
    assert whatsapp.outbox == [{"to": "+2348030000000", "text": "Town hall on Saturday\n\nDetails in the app."}]


def test_whatsapp_disabled_by_default(member):
    assert get_settings().whatsapp_enabled is False
    assert member.get("/api/users/me/preferences").json()["data"]["whatsapp_enabled"] is False


def test_untracked_database_stamping():
    assert untracked_revision({"users", "sources"}, {"whatsapp_events"}) == "1889870066a0"
    assert untracked_revision({"users", "sources"}, {"sms_events"}) == "c244e77c88be"
    assert untracked_revision({"users", "principal_profile"}) == "9a9061abd072"
    assert untracked_revision({"users", "alembic_version"}) is None
