"""Explicit response shapes. Member email/phone appear only in ``me`` (the
member's own account) and ``admin_member`` (for holders of members.view)."""

from __future__ import annotations

from .models import (
    AreaCouncil,
    Comment,
    Discussion,
    Event,
    News,
    Notification,
    Project,
    User,
)


def iso(dt):
    return dt.isoformat() if dt else None


def council_ref(c: AreaCouncil | None):
    if not c:
        return None
    return {"slug": c.slug, "name": c.name, "short_name": c.short_name}


def council(c: AreaCouncil, **extra) -> dict:
    return {
        "id": c.id,
        "slug": c.slug,
        "name": c.name,
        "short_name": c.short_name,
        "headquarters": c.headquarters,
        "summary": c.summary,
        "description": c.description,
        "image_url": c.image_url,
        "wards": [w.name for w in c.wards],
        **extra,
    }


def public_author(u: User | None) -> dict:
    """Public identity: display name only. Never email/phone."""
    if not u:
        return {"name": "Former member", "is_team": False}
    name = (u.profile.display_name if u.profile and u.profile.display_name else None) or u.full_name
    if u.deleted_at:
        name = "Former member"
    return {"id": u.id, "name": name, "is_team": bool(u.admin and u.admin.is_active)}


def me(u: User) -> dict:
    p = u.profile
    return {
        "id": u.id,
        "full_name": u.full_name,
        "first_name": u.first_name,
        "email": u.email,
        "phone": u.phone,
        "email_verified": u.email_verified_at is not None,
        "phone_verified": u.phone_verified_at is not None,
        "status": u.status,
        "created_at": iso(u.created_at),
        "area_council": council_ref(u.council_link.area_council) if u.council_link else None,
        "profile": {
            "display_name": p.display_name if p else None,
            "bio": p.bio if p else None,
            "avatar_url": p.avatar_url if p else None,
            "ward": p.ward_name if p else None,
            "community": p.community if p else None,
        },
        "admin": (
            {
                "role": u.admin.role.code,
                "role_name": u.admin.role.name,
                "area_council": council_ref(u.admin.area_council),
                "permissions": sorted(p.code for p in u.admin.role.permissions),
            }
            if u.admin and u.admin.is_active
            else None
        ),
    }


def preferences(p) -> dict:
    fields = [
        "in_app_announcements",
        "in_app_events",
        "in_app_community",
        "in_app_council_updates",
        "email_announcements",
        "email_events",
        "email_community",
        "sms_announcements",
        "sms_events",
    ]
    return {f: getattr(p, f) for f in fields}


def project_card(p: Project) -> dict:
    cover = p.images[0] if p.images else None
    return {
        "id": p.id,
        "slug": p.slug,
        "title": p.title,
        "category": {"slug": p.category.slug, "name": p.category.name},
        "area_council": council_ref(p.area_council),
        "location": p.location,
        "year": p.year,
        "record_date": iso(p.record_date),
        "summary": p.summary,
        "verification_status": p.verification_status,
        "is_featured": p.is_featured,
        "is_demo": p.is_demo,
        "image": {"url": cover.url, "alt": cover.alt} if cover else None,
        "source_count": len(p.sources),
        "published_at": iso(p.published_at),
    }


def project_detail(p: Project) -> dict:
    return {
        **project_card(p),
        "description": p.description,
        "verification_note": p.verification_note,
        "images": [
            {"url": i.url, "alt": i.alt, "caption": i.caption, "credit": i.credit} for i in p.images
        ],
        "documents": [{"title": d.title, "url": d.url, "file_type": d.file_type} for d in p.documents],
        "sources": [
            {
                "title": s.title,
                "publisher": s.publisher,
                "url": s.url,
                "published_on": iso(s.published_on),
                "notes": s.notes,
            }
            for s in p.sources
        ],
        "view_count": p.view_count,
        "updated_at": iso(p.updated_at),
    }


def project_admin(p: Project) -> dict:
    return {**project_detail(p), "status": p.status, "created_at": iso(p.created_at)}


def news_card(n: News) -> dict:
    return {
        "id": n.id,
        "slug": n.slug,
        "title": n.title,
        "excerpt": n.excerpt,
        "category": {"slug": n.category.slug, "name": n.category.name},
        "area_council": council_ref(n.area_council),
        "content_label": n.content_label,
        "image_url": n.image_url,
        "image_alt": n.image_alt,
        "author_name": n.author_name,
        "is_demo": n.is_demo,
        "is_featured": n.is_featured,
        "published_at": iso(n.published_at),
    }


def news_detail(n: News) -> dict:
    return {**news_card(n), "body": n.body, "source_note": n.source_note, "updated_at": iso(n.updated_at)}


def news_admin(n: News) -> dict:
    return {**news_detail(n), "status": n.status, "view_count": n.view_count, "created_at": iso(n.created_at)}


def event_card(e: Event, registered_count: int | None = None, is_registered: bool | None = None) -> dict:
    d = {
        "id": e.id,
        "slug": e.slug,
        "title": e.title,
        "summary": e.summary,
        "starts_at": iso(e.starts_at),
        "ends_at": iso(e.ends_at),
        "location": e.location,
        "area_council": council_ref(e.area_council),
        "image_url": e.image_url,
        "organizer": e.organizer,
        "registration_open": e.registration_open,
        "capacity": e.capacity,
        "status": e.status,
        "is_demo": e.is_demo,
    }
    if registered_count is not None:
        d["registered_count"] = registered_count
        d["spots_left"] = None if e.capacity is None else max(0, e.capacity - registered_count)
    if is_registered is not None:
        d["is_registered"] = is_registered
    return d


def event_detail(e: Event, **kw) -> dict:
    return {**event_card(e, **kw), "description": e.description}


def discussion(d: Discussion, liked: bool | None = None) -> dict:
    return {
        "id": d.id,
        "title": d.title,
        "body": d.body if d.status == "visible" else "[This discussion has been removed by moderators.]",
        "category": {"slug": d.category.slug, "name": d.category.name},
        "area_council": council_ref(d.area_council),
        "author": public_author(d.author),
        "status": d.status,
        "is_pinned": d.is_pinned,
        "is_locked": d.is_locked,
        "is_demo": d.is_demo,
        "comment_count": d.comment_count,
        "reaction_count": d.reaction_count,
        "liked": liked,
        "created_at": iso(d.created_at),
        "last_activity_at": iso(d.last_activity_at),
    }


def comment(c: Comment, liked: bool | None = None) -> dict:
    visible = c.status == "visible" and c.deleted_at is None
    return {
        "id": c.id,
        "parent_id": c.parent_id,
        "author": public_author(c.author) if visible else {"name": "—", "is_team": False},
        "body": c.body if visible else "[Comment removed]",
        "status": "deleted" if c.deleted_at else c.status,
        "reaction_count": c.reaction_count,
        "liked": liked,
        "created_at": iso(c.created_at),
    }


def notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "link": n.link,
        "read": n.read_at is not None,
        "created_at": iso(n.created_at),
    }


def announcement(a) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "body": a.body,
        "link_url": a.link_url,
        "area_council": council_ref(a.area_council),
        "priority": a.priority,
        "status": a.status,
        "publish_at": iso(a.publish_at),
        "expires_at": iso(a.expires_at),
        "is_demo": a.is_demo,
        "created_at": iso(a.created_at),
    }


def admin_member(u: User, include_contact: bool) -> dict:
    d = {
        "id": u.id,
        "full_name": u.full_name,
        "status": u.status,
        "suspended_reason": u.suspended_reason,
        "email_verified": u.email_verified_at is not None,
        "phone_verified": u.phone_verified_at is not None,
        "area_council": council_ref(u.council_link.area_council) if u.council_link else None,
        "ward": u.profile.ward_name if u.profile else None,
        "created_at": iso(u.created_at),
        "last_login_at": iso(u.last_login_at),
        "role": u.admin.role.code if u.admin and u.admin.is_active else None,
        "preferences": preferences(u.preferences) if u.preferences else None,
    }
    if include_contact:
        d["email"] = u.email
        d["phone"] = u.phone
    return d
