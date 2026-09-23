from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from .. import serializers as ser
from ..config import get_settings
from ..database import get_db
from ..deps import csrf_protect, get_current_user
from ..errors import ApiError
from ..models import (
    Announcement,
    AreaCouncil,
    Discussion,
    Event,
    EventRegistration,
    MemberAreaCouncil,
    News,
    Notification,
    NotificationPreference,
    Profile,
    Project,
    User,
    utcnow,
)
from ..responses import ok
from ..schemas import ChangePasswordIn, DeleteAccountIn, PreferencesIn, ProfileUpdateIn
from ..security import SESSION_COOKIE, hash_password, validate_password_strength, verify_password
from ..services.audit import audit
from .auth import revoke_all_sessions

router = APIRouter(prefix="/api/users", tags=["users"])
members = APIRouter(prefix="/api/members", tags=["members"])


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return ok(ser.me(user))


@router.patch("/me", dependencies=[Depends(csrf_protect)])
def update_me(body: ProfileUpdateIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    if user.profile is None:
        user.profile = Profile()
    if "full_name" in data and data["full_name"]:
        user.full_name = data["full_name"]
    for f in ("display_name", "bio", "community"):
        if f in data:
            setattr(user.profile, f, data[f] or None)
    if "ward" in data:
        user.profile.ward_name = data["ward"] or None
    if "phone" in data and data["phone"] != user.phone:
        if data["phone"] and db.scalar(select(User.id).where(User.phone == data["phone"], User.id != user.id)):
            raise ApiError(409, "phone_taken", "That phone number is already linked to another account.")
        user.phone = data["phone"]
        user.phone_verified_at = None
    if data.get("area_council"):
        council = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == data["area_council"]))
        if not council:
            raise ApiError(422, "invalid_area_council", "Please choose one of the six FCT Area Councils.")
        if user.council_link:
            user.council_link.area_council_id = council.id
        else:
            user.council_link = MemberAreaCouncil(area_council_id=council.id)
    audit(db, user.id, "member.profile_updated", "user", user.id, request, fields=sorted(data))
    db.commit()
    db.refresh(user)
    return ok(ser.me(user))


@router.get("/me/preferences")
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.preferences:
        user.preferences = NotificationPreference()
        db.commit()
    return ok({**ser.preferences(user.preferences), "sms_enabled": get_settings().sms_enabled})


@router.put("/me/preferences", dependencies=[Depends(csrf_protect)])
def put_preferences(body: PreferencesIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.preferences:
        user.preferences = NotificationPreference()
    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(user.preferences, k, v)
    audit(db, user.id, "member.preferences_updated", "user", user.id, request, changes=changes)
    db.commit()
    return ok({**ser.preferences(user.preferences), "sms_enabled": get_settings().sms_enabled})


@router.post("/me/password", dependencies=[Depends(csrf_protect)])
def change_password(body: ChangePasswordIn, request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise ApiError(400, "invalid_password", "Your current password is incorrect.")
    validate_password_strength(body.new_password)
    user.password_hash = hash_password(body.new_password)
    # Sign out every other session.
    revoke_all_sessions(db, user.id, except_id=getattr(request.state, "session_id", None))
    audit(db, user.id, "member.password_changed", "user", user.id, request)
    db.commit()
    return ok({"changed": True})


@router.delete("/me", dependencies=[Depends(csrf_protect)])
def delete_account(body: DeleteAccountIn, request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soft-delete and anonymise the account. Posts remain as 'Former member'."""
    if not verify_password(body.password, user.password_hash):
        raise ApiError(400, "invalid_password", "Your password is incorrect.")
    if user.admin and user.admin.is_active and user.admin.role.code == "super_admin":
        raise ApiError(400, "admin_account", "Transfer super admin access before deleting this account.")
    now = utcnow()
    user.deleted_at = now
    user.email = f"deleted-{user.id}@deleted.invalid"
    user.phone = None
    user.full_name = "Former member"
    user.password_hash = hash_password(f"deleted-{now.timestamp()}")
    if user.profile:
        user.profile.display_name = None
        user.profile.bio = None
        user.profile.community = None
        user.profile.ward_name = None
    revoke_all_sessions(db, user.id)
    audit(db, user.id, "member.account_deleted", "user", user.id, request)
    db.commit()
    response.delete_cookie(SESSION_COOKIE, path="/")
    return ok({"deleted": True})


@members.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = utcnow()
    council_id = user.council_link.area_council_id if user.council_link else None
    council = db.get(AreaCouncil, council_id) if council_id else None

    news_stmt = select(News).where(News.status == "published", News.deleted_at.is_(None))
    if council_id:
        news_stmt = news_stmt.where(or_(News.area_council_id == council_id, News.area_council_id.is_(None)))
    latest = db.scalars(news_stmt.order_by(News.published_at.desc()).limit(4)).unique().all()

    ev_stmt = select(Event).where(Event.status == "published", Event.deleted_at.is_(None), Event.starts_at >= now)
    upcoming = db.scalars(ev_stmt.order_by(Event.starts_at).limit(4)).unique().all()
    registered_ids = set(
        db.scalars(
            select(EventRegistration.event_id).where(
                EventRegistration.user_id == user.id, EventRegistration.status == "registered"
            )
        ).all()
    )

    records = db.scalars(
        select(Project)
        .where(Project.status == "published", Project.deleted_at.is_(None))
        .order_by(Project.published_at.desc())
        .limit(3)
    ).unique().all()

    notes = db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(5)
    ).all()
    unread = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )

    ann_stmt = select(Announcement).where(
        Announcement.status == "published",
        or_(Announcement.publish_at.is_(None), Announcement.publish_at <= now),
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
    )
    if council_id:
        ann_stmt = ann_stmt.where(or_(Announcement.area_council_id.is_(None), Announcement.area_council_id == council_id))
    else:
        ann_stmt = ann_stmt.where(Announcement.area_council_id.is_(None))
    announcements = db.scalars(ann_stmt.order_by(Announcement.created_at.desc()).limit(3)).unique().all()

    discussions = db.scalars(
        select(Discussion)
        .where(Discussion.status == "visible", Discussion.deleted_at.is_(None))
        .order_by(Discussion.last_activity_at.desc())
        .limit(4)
    ).unique().all()

    council_members = (
        db.scalar(
            select(func.count())
            .select_from(MemberAreaCouncil)
            .join(User, and_(User.id == MemberAreaCouncil.user_id, User.deleted_at.is_(None)))
            .where(MemberAreaCouncil.area_council_id == council_id)
        )
        if council_id
        else 0
    )

    return ok(
        {
            "user": ser.me(user),
            "area_council": ser.council(council, member_count=council_members) if council else None,
            "announcements": [ser.announcement(a) for a in announcements],
            "latest_updates": [ser.news_card(n) for n in latest],
            "upcoming_events": [ser.event_card(e, is_registered=e.id in registered_ids) for e in upcoming],
            "my_event_count": len(registered_ids),
            "featured_records": [ser.project_card(p) for p in records],
            "notifications": [ser.notification(n) for n in notes],
            "unread_notifications": unread or 0,
            "discussions": [ser.discussion(d) for d in discussions],
        }
    )
