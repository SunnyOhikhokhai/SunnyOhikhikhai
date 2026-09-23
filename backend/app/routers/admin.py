"""Administration API. Every route requires an active admin assignment and the
relevant permission; Area Council admins are restricted to their council."""

from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from .. import serializers as ser
from ..database import get_db
from ..deps import AdminContext, csrf_protect, get_admin, require
from ..errors import ApiError, forbidden, not_found
from ..models import (
    AdminUser,
    Announcement,
    AreaCouncil,
    AuditLog,
    Comment,
    ContactMessage,
    ContentViewStat,
    Discussion,
    Event,
    EventRegistration,
    MemberAreaCouncil,
    News,
    NewsCategory,
    Project,
    ProjectCategory,
    ProjectDocument,
    ProjectImage,
    ProjectSource,
    Report,
    Role,
    User,
    Ward,
    utcnow,
)
from ..responses import ok, paginate
from ..schemas import (
    AdminAssignIn,
    AnnouncementIn,
    CouncilIn,
    EventIn,
    ModerateIn,
    NewsIn,
    ProjectIn,
    ResolveReportIn,
    SuspendIn,
)
from ..services.audit import audit
from ..services.notify import audience, notify_users
from ..services.storage import store_upload
from ..utils import like_term, unique_slug
from .auth import revoke_all_sessions

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(csrf_protect)])


def _council(db: Session, slug: str | None) -> AreaCouncil | None:
    if not slug:
        return None
    c = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == slug))
    if not c:
        raise ApiError(422, "invalid_area_council", "Unknown Area Council.")
    return c


def _scope(stmt, model, ctx: AdminContext):
    if ctx.admin.role.is_scoped:
        return stmt.where(model.area_council_id == ctx.scoped_council_id)
    return stmt


def _check_scope(ctx: AdminContext, area_council_id: int | None) -> None:
    if ctx.admin.role.is_scoped:
        ctx.ensure_council(area_council_id)


# ---------------------------------------------------------------------------
# Session / overview
# ---------------------------------------------------------------------------


@router.get("/me")
def admin_me(ctx: AdminContext = Depends(get_admin)):
    return ok(
        {
            "user": ser.me(ctx.user),
            "role": ctx.role,
            "role_name": ctx.admin.role.name,
            "area_council": ser.council_ref(ctx.admin.area_council),
            "permissions": sorted(ctx.permissions),
        }
    )


def _days(n: int) -> list[date]:
    today = utcnow().date()
    return [today - timedelta(days=i) for i in range(n - 1, -1, -1)]


@router.get("/stats")
def stats(ctx: AdminContext = Depends(require("analytics.view", "members.view")), db: Session = Depends(get_db)):
    now = utcnow()
    live = User.deleted_at.is_(None)
    count = lambda stmt: db.scalar(stmt) or 0  # noqa: E731
    total = count(select(func.count()).select_from(User).where(live))
    verified = count(select(func.count()).select_from(User).where(live, User.email_verified_at.is_not(None)))
    new_7 = count(select(func.count()).select_from(User).where(live, User.created_at >= now - timedelta(days=7)))
    new_30 = count(select(func.count()).select_from(User).where(live, User.created_at >= now - timedelta(days=30)))
    active_30 = count(select(func.count()).select_from(User).where(live, User.last_seen_at >= now - timedelta(days=30)))
    event_regs = count(select(func.count()).select_from(EventRegistration).where(EventRegistration.status == "registered"))
    news_views = count(select(func.sum(News.view_count)))
    record_views = count(select(func.sum(Project.view_count)))
    discussions = count(select(func.count()).select_from(Discussion).where(Discussion.deleted_at.is_(None)))
    comments_30 = count(select(func.count()).select_from(Comment).where(Comment.created_at >= now - timedelta(days=30)))
    open_reports = count(select(func.count()).select_from(Report).where(Report.status == "open"))

    by_council = db.execute(
        select(AreaCouncil.slug, AreaCouncil.short_name, func.count(MemberAreaCouncil.id))
        .select_from(AreaCouncil)
        .outerjoin(MemberAreaCouncil, MemberAreaCouncil.area_council_id == AreaCouncil.id)
        .outerjoin(User, (User.id == MemberAreaCouncil.user_id))
        .where(or_(User.id.is_(None), User.deleted_at.is_(None)))
        .group_by(AreaCouncil.id, AreaCouncil.slug, AreaCouncil.short_name, AreaCouncil.sort_order)
        .order_by(AreaCouncil.sort_order)
    ).all()

    # Registration trend (30 days) and membership growth (12 months), computed
    # in Python for database portability.
    joined = db.scalars(select(User.created_at).where(live)).all()
    per_day = Counter(d.date() for d in joined)
    trend = [{"date": d.isoformat(), "registrations": per_day.get(d, 0)} for d in _days(30)]
    months = []
    first = utcnow().date().replace(day=1)
    for i in range(11, -1, -1):
        y, m = first.year, first.month - i
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))
    growth = []
    for y, m in months:
        end = date(y + (m == 12), (m % 12) + 1, 1)
        growth.append({"month": f"{y}-{m:02d}", "members": sum(1 for d in joined if d.date() < end)})

    return ok(
        {
            "totals": {
                "members": total,
                "verified_members": verified,
                "new_registrations_7d": new_7,
                "new_registrations_30d": new_30,
                "active_users_30d": active_30,
                "event_registrations": event_regs,
                "news_views": news_views,
                "record_views": record_views,
                "discussions": discussions,
                "comments_30d": comments_30,
                "open_reports": open_reports,
            },
            "by_council": [{"slug": s, "name": n, "members": c} for s, n, c in by_council],
            "registration_trend": trend,
            "membership_growth": growth,
        }
    )


@router.get("/analytics")
def analytics(
    days: int = Query(30, ge=7, le=365),
    ctx: AdminContext = Depends(require("analytics.view")),
    db: Session = Depends(get_db),
):
    since = utcnow().date() - timedelta(days=days - 1)
    rows = db.execute(
        select(ContentViewStat.day, ContentViewStat.content_type, func.sum(ContentViewStat.views))
        .where(ContentViewStat.day >= since)
        .group_by(ContentViewStat.day, ContentViewStat.content_type)
    ).all()
    views: dict[date, dict[str, int]] = defaultdict(dict)
    for d, t, v in rows:
        views[d][t] = int(v or 0)
    engagement = [
        {"date": d.isoformat(), **{t: views[d].get(t, 0) for t in ("project", "news", "event")}} for d in _days(days)
    ]
    since_dt = utcnow() - timedelta(days=days)
    disc = Counter(d.date() for d in db.scalars(select(Discussion.created_at).where(Discussion.created_at >= since_dt)))
    comm = Counter(d.date() for d in db.scalars(select(Comment.created_at).where(Comment.created_at >= since_dt)))
    regs = Counter(
        d.date() for d in db.scalars(select(EventRegistration.created_at).where(EventRegistration.created_at >= since_dt))
    )
    community = [
        {"date": d.isoformat(), "discussions": disc.get(d, 0), "comments": comm.get(d, 0), "event_registrations": regs.get(d, 0)}
        for d in _days(days)
    ]
    popular_records = db.scalars(
        select(Project).where(Project.deleted_at.is_(None), Project.status == "published").order_by(Project.view_count.desc()).limit(5)
    ).unique().all()
    popular_news = db.scalars(
        select(News).where(News.deleted_at.is_(None), News.status == "published").order_by(News.view_count.desc()).limit(5)
    ).unique().all()
    top_events = db.execute(
        select(Event.title, Event.slug, func.count(EventRegistration.id))
        .join(EventRegistration, EventRegistration.event_id == Event.id)
        .where(EventRegistration.status == "registered")
        .group_by(Event.id, Event.title, Event.slug)
        .order_by(func.count(EventRegistration.id).desc())
        .limit(5)
    ).all()
    return ok(
        {
            "engagement": engagement,
            "community": community,
            "popular_records": [{"title": p.title, "slug": p.slug, "views": p.view_count} for p in popular_records],
            "popular_news": [{"title": n.title, "slug": n.slug, "views": n.view_count} for n in popular_news],
            "top_events": [{"title": t, "slug": s, "registrations": c} for t, s, c in top_events],
        }
    )


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


def _members_query(q: str | None, area_council: str | None, status: str | None, verified: bool | None, db: Session):
    stmt = (
        select(User)
        .options(selectinload(User.council_link), selectinload(User.profile), selectinload(User.preferences))
        .where(User.deleted_at.is_(None))
    )
    if q:
        t = like_term(q)
        stmt = stmt.where(or_(User.full_name.ilike(t), User.email.ilike(t), User.phone.ilike(t)))
    if area_council:
        c = _council(db, area_council)
        stmt = stmt.join(MemberAreaCouncil, MemberAreaCouncil.user_id == User.id).where(
            MemberAreaCouncil.area_council_id == c.id
        )
    if status:
        stmt = stmt.where(User.status == status)
    if verified is not None:
        stmt = stmt.where(User.email_verified_at.is_not(None) if verified else User.email_verified_at.is_(None))
    return stmt


@router.get("/members")
def list_members(
    q: str | None = Query(None, max_length=100),
    area_council: str | None = None,
    status: str | None = Query(None, pattern="^(active|suspended)$"),
    verified: bool | None = None,
    page: int = 1,
    page_size: int = 25,
    ctx: AdminContext = Depends(require("members.view", "members.suspend")),
    db: Session = Depends(get_db),
):
    include_contact = ctx.has("members.view")
    if q and not include_contact:
        # Moderators may search by name only.
        stmt = _members_query(None, area_council, status, verified, db).where(User.full_name.ilike(like_term(q)))
    else:
        stmt = _members_query(q, area_council, status, verified, db)
    return paginate(
        db, stmt.order_by(User.created_at.desc()), page, page_size, lambda u: ser.admin_member(u, include_contact)
    )


@router.get("/members/export")
def export_members(
    request: Request,
    area_council: str | None = None,
    ctx: AdminContext = Depends(require("members.export")),
    db: Session = Depends(get_db),
):
    """CSV of permitted data. Email addresses are included only for members who
    opted in to email communications; phone numbers are never exported."""
    users = db.scalars(_members_query(None, area_council, None, None, db).order_by(User.created_at)).all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "full_name", "area_council", "ward", "status", "email_verified", "joined", "email_opt_in", "email"])
    for u in users:
        p = u.preferences
        opted = bool(p and (p.email_announcements or p.email_events))
        w.writerow(
            [
                u.id,
                u.full_name,
                u.council_link.area_council.short_name if u.council_link else "",
                u.profile.ward_name if u.profile and u.profile.ward_name else "",
                u.status,
                "yes" if u.email_verified_at else "no",
                u.created_at.date().isoformat(),
                "yes" if opted else "no",
                u.email if opted else "",
            ]
        )
    audit(db, ctx.user.id, "members.exported", None, None, request, count=len(users), area_council=area_council)
    db.commit()
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="nipam-members.csv"'},
    )


@router.get("/members/{uid}")
def get_member(uid: int, ctx: AdminContext = Depends(require("members.view", "members.suspend")), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.deleted_at:
        raise not_found("Member")
    discussions = db.scalar(select(func.count()).select_from(Discussion).where(Discussion.author_id == uid)) or 0
    comments = db.scalar(select(func.count()).select_from(Comment).where(Comment.author_id == uid)) or 0
    reports = db.scalar(
        select(func.count())
        .select_from(Report)
        .where(
            or_(
                (Report.target_type == "discussion") & Report.target_id.in_(select(Discussion.id).where(Discussion.author_id == uid)),
                (Report.target_type == "comment") & Report.target_id.in_(select(Comment.id).where(Comment.author_id == uid)),
            )
        )
    ) or 0
    return ok(
        {
            **ser.admin_member(u, ctx.has("members.view")),
            "activity": {"discussions": discussions, "comments": comments, "reports_against": reports},
        }
    )


@router.post("/members/{uid}/suspend")
def suspend_member(uid: int, body: SuspendIn, request: Request, ctx: AdminContext = Depends(require("members.suspend")), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.deleted_at:
        raise not_found("Member")
    if u.id == ctx.user.id:
        raise ApiError(400, "self_action", "You cannot suspend your own account.")
    if u.admin and u.admin.is_active and ctx.role != "super_admin":
        raise forbidden("Only a Super Admin can suspend an administrator.")
    u.status = "suspended"
    u.suspended_reason = body.reason
    revoke_all_sessions(db, u.id)
    audit(db, ctx.user.id, "member.suspended", "user", u.id, request, reason=body.reason)
    db.commit()
    return ok(ser.admin_member(u, ctx.has("members.view")))


@router.post("/members/{uid}/reactivate")
def reactivate_member(uid: int, request: Request, ctx: AdminContext = Depends(require("members.suspend")), db: Session = Depends(get_db)):
    u = db.get(User, uid)
    if not u or u.deleted_at:
        raise not_found("Member")
    u.status = "active"
    u.suspended_reason = None
    audit(db, ctx.user.id, "member.reactivated", "user", u.id, request)
    db.commit()
    notify_users(db, [u], "account", "Your account has been reactivated", "You can log in and take part again.")
    return ok(ser.admin_member(u, ctx.has("members.view")))


@router.put("/members/{uid}/preferences")
def admin_update_preferences(
    uid: int, body: dict, request: Request, ctx: AdminContext = Depends(require("members.view")), db: Session = Depends(get_db)
):
    """Record a member's request to change communications (e.g. an opt-out
    received by phone). Admins may only switch channels off, never on."""
    u = db.get(User, uid)
    if not u or not u.preferences:
        raise not_found("Member")
    changed = {}
    for k, v in body.items():
        if hasattr(u.preferences, k) and k.startswith(("email_", "sms_", "in_app_")) and v is False:
            setattr(u.preferences, k, False)
            changed[k] = False
    audit(db, ctx.user.id, "member.preferences_opt_out", "user", u.id, request, changes=changed)
    db.commit()
    return ok(ser.preferences(u.preferences))


# ---------------------------------------------------------------------------
# Records (Our Record)
# ---------------------------------------------------------------------------


def _apply_project(db: Session, p: Project, body: ProjectIn, ctx: AdminContext) -> None:
    cat = db.scalar(select(ProjectCategory).where(ProjectCategory.slug == body.category))
    if not cat:
        raise ApiError(422, "invalid_category", "Unknown record category.")
    council = _council(db, body.area_council)
    _check_scope(ctx, council.id if council else None)
    if body.verification_status != p.verification_status and not ctx.has("records.verify"):
        raise forbidden("You cannot change verification status.")
    if body.verification_status == "verified" and not body.sources:
        raise ApiError(422, "source_required", "A record can only be marked verified when at least one source is provided.")
    p.title = body.title
    p.category_id = cat.id
    p.area_council_id = council.id if council else None
    p.location = body.location
    p.year = body.year
    p.record_date = body.record_date
    p.summary = body.summary
    p.description = body.description
    p.verification_status = body.verification_status
    p.verification_note = body.verification_note
    p.is_featured = body.is_featured
    p.is_demo = body.is_demo
    p.sources = [ProjectSource(**s.model_dump()) for s in body.sources]
    p.images = [ProjectImage(sort_order=i, **img.model_dump()) for i, img in enumerate(body.images)]
    p.documents = [ProjectDocument(**d.model_dump()) for d in body.documents]


@router.get("/projects")
def admin_projects(
    q: str | None = Query(None, max_length=100),
    status: str | None = Query(None, pattern="^(draft|published)$"),
    page: int = 1,
    page_size: int = 20,
    ctx: AdminContext = Depends(require("records.manage")),
    db: Session = Depends(get_db),
):
    stmt = select(Project).where(Project.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Project.title.ilike(like_term(q)))
    if status:
        stmt = stmt.where(Project.status == status)
    return paginate(db, _scope(stmt, Project, ctx).order_by(Project.updated_at.desc()), page, page_size, ser.project_admin)


def _project(db: Session, pid: int, ctx: AdminContext) -> Project:
    p = db.get(Project, pid)
    if not p or p.deleted_at:
        raise not_found("Record")
    _check_scope(ctx, p.area_council_id)
    return p


@router.get("/projects/{pid}")
def admin_project(pid: int, ctx: AdminContext = Depends(require("records.manage")), db: Session = Depends(get_db)):
    return ok(ser.project_admin(_project(db, pid, ctx)))


@router.post("/projects", status_code=201)
def create_project(body: ProjectIn, request: Request, ctx: AdminContext = Depends(require("records.manage")), db: Session = Depends(get_db)):
    p = Project(slug=unique_slug(db, Project, body.title), created_by_id=ctx.user.id, verification_status="unverified")
    _apply_project(db, p, body, ctx)
    db.add(p)
    db.flush()
    audit(db, ctx.user.id, "record.created", "project", p.id, request)
    db.commit()
    return ok(ser.project_admin(p))


@router.put("/projects/{pid}")
def update_project(pid: int, body: ProjectIn, request: Request, ctx: AdminContext = Depends(require("records.manage")), db: Session = Depends(get_db)):
    p = _project(db, pid, ctx)
    before = p.verification_status
    _apply_project(db, p, body, ctx)
    audit(db, ctx.user.id, "record.updated", "project", p.id, request, verification=[before, p.verification_status])
    db.commit()
    return ok(ser.project_admin(p))


@router.post("/projects/{pid}/publish")
def publish_project(pid: int, request: Request, ctx: AdminContext = Depends(require("records.manage")), db: Session = Depends(get_db)):
    p = _project(db, pid, ctx)
    p.status = "published"
    p.published_at = p.published_at or utcnow()
    audit(db, ctx.user.id, "record.published", "project", p.id, request)
    db.commit()
    return ok(ser.project_admin(p))


@router.post("/projects/{pid}/unpublish")
def unpublish_project(pid: int, request: Request, ctx: AdminContext = Depends(require("records.manage")), db: Session = Depends(get_db)):
    p = _project(db, pid, ctx)
    p.status = "draft"
    audit(db, ctx.user.id, "record.unpublished", "project", p.id, request)
    db.commit()
    return ok(ser.project_admin(p))


@router.delete("/projects/{pid}")
def delete_project(pid: int, request: Request, ctx: AdminContext = Depends(require("records.manage")), db: Session = Depends(get_db)):
    p = _project(db, pid, ctx)
    p.deleted_at = utcnow()
    p.status = "draft"
    audit(db, ctx.user.id, "record.deleted", "project", p.id, request)
    db.commit()
    return ok({"deleted": True})


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------


def _apply_news(db: Session, n: News, body: NewsIn, ctx: AdminContext) -> None:
    cat = db.scalar(select(NewsCategory).where(NewsCategory.slug == body.category))
    if not cat:
        raise ApiError(422, "invalid_category", "Unknown news category.")
    council = _council(db, body.area_council)
    _check_scope(ctx, council.id if council else None)
    if body.content_label == "verified_information" and not body.source_note:
        raise ApiError(422, "source_required", "Content labelled as verified information must cite a source.")
    for f in ("title", "excerpt", "body", "content_label", "source_note", "image_url", "image_alt", "author_name", "is_featured", "is_demo"):
        setattr(n, f, getattr(body, f))
    n.category_id = cat.id
    n.area_council_id = council.id if council else None


def _news(db: Session, nid: int, ctx: AdminContext) -> News:
    n = db.get(News, nid)
    if not n or n.deleted_at:
        raise not_found("Article")
    _check_scope(ctx, n.area_council_id)
    return n


@router.get("/news")
def admin_news(
    q: str | None = Query(None, max_length=100),
    status: str | None = Query(None, pattern="^(draft|published)$"),
    page: int = 1,
    page_size: int = 20,
    ctx: AdminContext = Depends(require("news.manage")),
    db: Session = Depends(get_db),
):
    stmt = select(News).where(News.deleted_at.is_(None))
    if q:
        stmt = stmt.where(News.title.ilike(like_term(q)))
    if status:
        stmt = stmt.where(News.status == status)
    return paginate(db, _scope(stmt, News, ctx).order_by(News.updated_at.desc()), page, page_size, ser.news_admin)


@router.get("/news/{nid}")
def admin_news_item(nid: int, ctx: AdminContext = Depends(require("news.manage")), db: Session = Depends(get_db)):
    return ok(ser.news_admin(_news(db, nid, ctx)))


@router.post("/news", status_code=201)
def create_news(body: NewsIn, request: Request, ctx: AdminContext = Depends(require("news.manage")), db: Session = Depends(get_db)):
    n = News(slug=unique_slug(db, News, body.title), created_by_id=ctx.user.id)
    _apply_news(db, n, body, ctx)
    db.add(n)
    db.flush()
    audit(db, ctx.user.id, "news.created", "news", n.id, request)
    db.commit()
    return ok(ser.news_admin(n))


@router.put("/news/{nid}")
def update_news(nid: int, body: NewsIn, request: Request, ctx: AdminContext = Depends(require("news.manage")), db: Session = Depends(get_db)):
    n = _news(db, nid, ctx)
    _apply_news(db, n, body, ctx)
    audit(db, ctx.user.id, "news.updated", "news", n.id, request)
    db.commit()
    return ok(ser.news_admin(n))


@router.post("/news/{nid}/publish")
def publish_news(nid: int, request: Request, tasks: BackgroundTasks, ctx: AdminContext = Depends(require("news.manage")), db: Session = Depends(get_db)):
    n = _news(db, nid, ctx)
    first = n.published_at is None
    n.status = "published"
    n.published_at = n.published_at or utcnow()
    audit(db, ctx.user.id, "news.published", "news", n.id, request)
    db.commit()
    if first and n.area_council_id:
        notify_users(
            db, audience(db, n.area_council_id), "council_update",
            f"{n.area_council.short_name} update: {n.title}", n.excerpt, f"/news/{n.slug}", tasks,
        )
    return ok(ser.news_admin(n))


@router.post("/news/{nid}/unpublish")
def unpublish_news(nid: int, request: Request, ctx: AdminContext = Depends(require("news.manage")), db: Session = Depends(get_db)):
    n = _news(db, nid, ctx)
    n.status = "draft"
    audit(db, ctx.user.id, "news.unpublished", "news", n.id, request)
    db.commit()
    return ok(ser.news_admin(n))


@router.delete("/news/{nid}")
def delete_news(nid: int, request: Request, ctx: AdminContext = Depends(require("news.manage")), db: Session = Depends(get_db)):
    n = _news(db, nid, ctx)
    n.deleted_at = utcnow()
    n.status = "draft"
    audit(db, ctx.user.id, "news.deleted", "news", n.id, request)
    db.commit()
    return ok({"deleted": True})


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


def _apply_event(db: Session, e: Event, body: EventIn, ctx: AdminContext) -> None:
    council = _council(db, body.area_council)
    _check_scope(ctx, council.id if council else None)
    if body.ends_at and body.ends_at < body.starts_at:
        raise ApiError(422, "invalid_dates", "The event must end after it starts.")
    for f in ("title", "summary", "description", "starts_at", "ends_at", "location", "image_url", "organizer", "registration_open", "capacity", "is_demo"):
        setattr(e, f, getattr(body, f))
    e.area_council_id = council.id if council else None


def _event(db: Session, eid: int, ctx: AdminContext) -> Event:
    e = db.get(Event, eid)
    if not e or e.deleted_at:
        raise not_found("Event")
    _check_scope(ctx, e.area_council_id)
    return e


def _event_admin(db: Session, e: Event) -> dict:
    n = db.scalar(
        select(func.count()).select_from(EventRegistration).where(EventRegistration.event_id == e.id, EventRegistration.status == "registered")
    ) or 0
    return {**ser.event_detail(e, registered_count=n), "view_count": e.view_count}


@router.get("/events")
def admin_events(
    q: str | None = Query(None, max_length=100),
    status: str | None = Query(None, pattern="^(draft|published|cancelled|archived)$"),
    page: int = 1,
    page_size: int = 20,
    ctx: AdminContext = Depends(require("events.manage")),
    db: Session = Depends(get_db),
):
    stmt = select(Event).where(Event.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Event.title.ilike(like_term(q)))
    if status:
        stmt = stmt.where(Event.status == status)
    return paginate(db, _scope(stmt, Event, ctx).order_by(Event.starts_at.desc()), page, page_size, lambda e: _event_admin(db, e))


@router.get("/events/{eid}")
def admin_event(eid: int, ctx: AdminContext = Depends(require("events.manage")), db: Session = Depends(get_db)):
    return ok(_event_admin(db, _event(db, eid, ctx)))


@router.post("/events", status_code=201)
def create_event(body: EventIn, request: Request, ctx: AdminContext = Depends(require("events.manage")), db: Session = Depends(get_db)):
    e = Event(slug=unique_slug(db, Event, body.title), created_by_id=ctx.user.id)
    _apply_event(db, e, body, ctx)
    db.add(e)
    db.flush()
    audit(db, ctx.user.id, "event.created", "event", e.id, request)
    db.commit()
    return ok(_event_admin(db, e))


@router.put("/events/{eid}")
def update_event(eid: int, body: EventIn, request: Request, ctx: AdminContext = Depends(require("events.manage")), db: Session = Depends(get_db)):
    e = _event(db, eid, ctx)
    _apply_event(db, e, body, ctx)
    audit(db, ctx.user.id, "event.updated", "event", e.id, request)
    db.commit()
    return ok(_event_admin(db, e))


@router.post("/events/{eid}/status")
def event_status(
    eid: int,
    request: Request,
    tasks: BackgroundTasks,
    status: str = Query(pattern="^(draft|published|cancelled|archived)$"),
    ctx: AdminContext = Depends(require("events.manage")),
    db: Session = Depends(get_db),
):
    e = _event(db, eid, ctx)
    previous = e.status
    e.status = status
    audit(db, ctx.user.id, f"event.{status}", "event", e.id, request, previous=previous)
    db.commit()
    if status == "published" and not e.notified_at and e.starts_at > utcnow():
        e.notified_at = utcnow()
        db.commit()
        notify_users(db, audience(db, e.area_council_id), "event", f"New event: {e.title}", f"{e.location}", f"/events/{e.slug}", tasks)
    if status == "cancelled" and previous != "cancelled":
        registrants = list(
            db.scalars(
                select(User)
                .join(EventRegistration, EventRegistration.user_id == User.id)
                .where(EventRegistration.event_id == e.id, EventRegistration.status == "registered")
            ).all()
        )
        notify_users(db, registrants, "event", f"Event cancelled: {e.title}", "This event has been cancelled.", f"/events/{e.slug}", tasks)
    return ok(_event_admin(db, e))


@router.delete("/events/{eid}")
def delete_event(eid: int, request: Request, ctx: AdminContext = Depends(require("events.manage")), db: Session = Depends(get_db)):
    e = _event(db, eid, ctx)
    e.deleted_at = utcnow()
    audit(db, ctx.user.id, "event.deleted", "event", e.id, request)
    db.commit()
    return ok({"deleted": True})


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------


def _announcement(db: Session, aid: int, ctx: AdminContext) -> Announcement:
    a = db.get(Announcement, aid)
    if not a:
        raise not_found("Announcement")
    _check_scope(ctx, a.area_council_id)
    return a


def _apply_announcement(db: Session, a: Announcement, body: AnnouncementIn, ctx: AdminContext) -> None:
    council = _council(db, body.area_council)
    _check_scope(ctx, council.id if council else None)
    if body.expires_at and body.publish_at and body.expires_at <= body.publish_at:
        raise ApiError(422, "invalid_dates", "Expiry must be after the publish time.")
    for f in ("title", "body", "link_url", "priority", "publish_at", "expires_at"):
        setattr(a, f, getattr(body, f))
    a.area_council_id = council.id if council else None


def dispatch_announcement(db: Session, a: Announcement, tasks: BackgroundTasks | None = None) -> None:
    """Notify members once an announcement is live. Also used by the scheduler."""
    if a.notified_at or a.status != "published" or (a.publish_at and a.publish_at > utcnow()):
        return
    a.notified_at = utcnow()
    db.commit()
    notify_users(db, audience(db, a.area_council_id), "announcement", a.title, a.body[:300], a.link_url or "/notifications", tasks)


@router.get("/announcements")
def admin_announcements(page: int = 1, page_size: int = 20, ctx: AdminContext = Depends(require("announcements.manage")), db: Session = Depends(get_db)):
    stmt = _scope(select(Announcement), Announcement, ctx).order_by(Announcement.created_at.desc())
    return paginate(db, stmt, page, page_size, ser.announcement)


@router.post("/announcements", status_code=201)
def create_announcement(body: AnnouncementIn, request: Request, ctx: AdminContext = Depends(require("announcements.manage")), db: Session = Depends(get_db)):
    a = Announcement(created_by_id=ctx.user.id)
    _apply_announcement(db, a, body, ctx)
    db.add(a)
    db.flush()
    audit(db, ctx.user.id, "announcement.created", "announcement", a.id, request)
    db.commit()
    return ok(ser.announcement(a))


@router.put("/announcements/{aid}")
def update_announcement(aid: int, body: AnnouncementIn, request: Request, ctx: AdminContext = Depends(require("announcements.manage")), db: Session = Depends(get_db)):
    a = _announcement(db, aid, ctx)
    _apply_announcement(db, a, body, ctx)
    audit(db, ctx.user.id, "announcement.updated", "announcement", a.id, request)
    db.commit()
    return ok(ser.announcement(a))


@router.post("/announcements/{aid}/publish")
def publish_announcement(aid: int, request: Request, tasks: BackgroundTasks, ctx: AdminContext = Depends(require("announcements.manage")), db: Session = Depends(get_db)):
    a = _announcement(db, aid, ctx)
    a.status = "published"
    audit(db, ctx.user.id, "announcement.published", "announcement", a.id, request)
    db.commit()
    dispatch_announcement(db, a, tasks)
    return ok(ser.announcement(a))


@router.post("/announcements/{aid}/expire")
def expire_announcement(aid: int, request: Request, ctx: AdminContext = Depends(require("announcements.manage")), db: Session = Depends(get_db)):
    a = _announcement(db, aid, ctx)
    a.expires_at = utcnow()
    audit(db, ctx.user.id, "announcement.expired", "announcement", a.id, request)
    db.commit()
    return ok(ser.announcement(a))


@router.delete("/announcements/{aid}")
def delete_announcement(aid: int, request: Request, ctx: AdminContext = Depends(require("announcements.manage")), db: Session = Depends(get_db)):
    a = _announcement(db, aid, ctx)
    db.delete(a)
    audit(db, ctx.user.id, "announcement.deleted", "announcement", aid, request)
    db.commit()
    return ok({"deleted": True})


# ---------------------------------------------------------------------------
# Area Councils
# ---------------------------------------------------------------------------


@router.put("/area-councils/{slug}")
def update_council(slug: str, body: CouncilIn, request: Request, ctx: AdminContext = Depends(require("councils.manage")), db: Session = Depends(get_db)):
    c = _council(db, slug)
    _check_scope(ctx, c.id)
    data = body.model_dump(exclude_unset=True)
    wards = data.pop("wards", None)
    for k, v in data.items():
        setattr(c, k, v)
    if wards is not None:
        wanted = {w.strip() for w in wards if w and w.strip()}
        existing = {w.name: w for w in c.wards}
        for name, w in existing.items():
            if name not in wanted:
                db.delete(w)
        for name in wanted - set(existing):
            db.add(Ward(area_council_id=c.id, name=name[:120]))
    audit(db, ctx.user.id, "council.updated", "area_council", c.id, request, fields=sorted(data) + (["wards"] if wards is not None else []))
    db.commit()
    db.refresh(c)
    return ok(ser.council(c))


# ---------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------


def _report_target(db: Session, r: Report):
    model = Discussion if r.target_type == "discussion" else Comment
    return db.get(model, r.target_id)


@router.get("/reports")
def list_reports(
    status: str = Query("open", pattern="^(open|resolved|dismissed|all)$"),
    page: int = 1,
    page_size: int = 20,
    ctx: AdminContext = Depends(require("moderation.manage")),
    db: Session = Depends(get_db),
):
    stmt = select(Report)
    if status != "all":
        stmt = stmt.where(Report.status == status)

    def row(r: Report) -> dict:
        t = _report_target(db, r)
        target = None
        if t is not None:
            target = {
                "id": t.id,
                "title": getattr(t, "title", None),
                "body": t.body[:600],
                "status": t.status,
                "deleted": t.deleted_at is not None,
                "author": {"id": t.author_id, "name": t.author.full_name, "status": t.author.status},
                "discussion_id": t.id if r.target_type == "discussion" else t.discussion_id,
            }
        return {
            "id": r.id,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "reason": r.reason,
            "details": r.details,
            "status": r.status,
            "resolution_note": r.resolution_note,
            "created_at": ser.iso(r.created_at),
            "resolved_at": ser.iso(r.resolved_at),
            "reporter": r.reporter.full_name if r.reporter else None,
            "target": target,
        }

    return paginate(db, stmt.order_by(Report.created_at.desc()), page, page_size, row)


@router.post("/reports/{rid}/resolve")
def resolve_report(rid: int, body: ResolveReportIn, request: Request, ctx: AdminContext = Depends(require("moderation.manage")), db: Session = Depends(get_db)):
    r = db.get(Report, rid)
    if not r:
        raise not_found("Report")
    target = _report_target(db, r)
    now = utcnow()
    if body.action in ("remove_content", "hide_content", "suspend_author") and target is not None:
        target.status = "removed" if body.action != "hide_content" else "hidden"
        if body.action == "suspend_author":
            author = db.get(User, target.author_id)
            if author and not (author.admin and author.admin.is_active):
                author.status = "suspended"
                author.suspended_reason = f"Community guidelines violation ({r.reason})"
                revoke_all_sessions(db, author.id)
    # Resolve every open report for the same target together.
    related = db.scalars(
        select(Report).where(Report.target_type == r.target_type, Report.target_id == r.target_id, Report.status == "open")
    ).all()
    for rep in set(related) | {r}:
        rep.status = "dismissed" if body.action == "dismiss" else "resolved"
        rep.resolution_note = body.note
        rep.resolved_by_id = ctx.user.id
        rep.resolved_at = now
    if body.action == "dismiss" and target is not None and target.status == "hidden":
        target.status = "visible"  # restore auto-hidden content
    audit(db, ctx.user.id, f"moderation.{body.action}", r.target_type, r.target_id, request, report_id=r.id, note=body.note)
    db.commit()
    return ok({"resolved": True, "status": r.status})


@router.get("/discussions")
def admin_discussions(
    status: str | None = Query(None, pattern="^(visible|hidden|removed)$"),
    q: str | None = Query(None, max_length=100),
    page: int = 1,
    page_size: int = 20,
    ctx: AdminContext = Depends(require("moderation.manage")),
    db: Session = Depends(get_db),
):
    stmt = select(Discussion).where(Discussion.deleted_at.is_(None))
    if status:
        stmt = stmt.where(Discussion.status == status)
    if q:
        stmt = stmt.where(Discussion.title.ilike(like_term(q)))
    return paginate(db, stmt.order_by(Discussion.created_at.desc()), page, page_size, ser.discussion)


@router.patch("/discussions/{did}")
def moderate_discussion(did: int, body: ModerateIn, request: Request, ctx: AdminContext = Depends(require("moderation.manage")), db: Session = Depends(get_db)):
    d = db.get(Discussion, did)
    if not d:
        raise not_found("Discussion")
    changes = body.model_dump(exclude_none=True)
    for k, v in changes.items():
        setattr(d, k, v)
    audit(db, ctx.user.id, "moderation.discussion_updated", "discussion", d.id, request, changes=changes)
    db.commit()
    return ok(ser.discussion(d))


@router.patch("/comments/{cid}")
def moderate_comment(cid: int, body: ModerateIn, request: Request, ctx: AdminContext = Depends(require("moderation.manage")), db: Session = Depends(get_db)):
    c = db.get(Comment, cid)
    if not c or body.status is None:
        raise not_found("Comment")
    c.status = body.status
    audit(db, ctx.user.id, "moderation.comment_updated", "comment", c.id, request, status=body.status)
    db.commit()
    return ok(ser.comment(c))


# ---------------------------------------------------------------------------
# Administrators, audit, uploads, contact inbox
# ---------------------------------------------------------------------------


@router.get("/roles")
def list_roles(ctx: AdminContext = Depends(require("admins.manage")), db: Session = Depends(get_db)):
    roles = db.scalars(select(Role).order_by(Role.id)).all()
    return ok(
        [
            {"code": r.code, "name": r.name, "description": r.description, "scoped": r.is_scoped, "permissions": sorted(p.code for p in r.permissions)}
            for r in roles
        ]
    )


@router.get("/admins")
def list_admins(ctx: AdminContext = Depends(require("admins.manage")), db: Session = Depends(get_db)):
    admins = db.scalars(select(AdminUser).where(AdminUser.is_active.is_(True)).order_by(AdminUser.created_at)).all()
    return ok(
        [
            {
                "user_id": a.user_id,
                "name": a.user.full_name,
                "email": a.user.email,
                "role": a.role.code,
                "role_name": a.role.name,
                "area_council": ser.council_ref(a.area_council),
                "since": ser.iso(a.created_at),
            }
            for a in admins
        ]
    )


@router.post("/admins")
def assign_admin(body: AdminAssignIn, request: Request, ctx: AdminContext = Depends(require("admins.manage")), db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == body.email.lower(), User.deleted_at.is_(None)))
    if not u:
        raise ApiError(404, "not_found", "No member account uses that email. They must register first.")
    if not u.email_verified_at:
        raise ApiError(400, "unverified", "The member must verify their email before receiving an admin role.")
    role = db.scalar(select(Role).where(Role.code == body.role))
    council = _council(db, body.area_council)
    if role.is_scoped and not council:
        raise ApiError(422, "council_required", "Area Council admins need an assigned Area Council.")
    a = db.scalar(select(AdminUser).where(AdminUser.user_id == u.id))
    if a:
        a.role_id, a.is_active = role.id, True
        a.area_council_id = council.id if role.is_scoped else None
    else:
        db.add(AdminUser(user_id=u.id, role_id=role.id, area_council_id=council.id if role.is_scoped else None, created_by_id=ctx.user.id))
    audit(db, ctx.user.id, "admin.assigned", "user", u.id, request, role=body.role, area_council=body.area_council)
    db.commit()
    notify_users(db, [u], "account", f"You have been given the {role.name} role", "Open the admin dashboard to get started.", "/admin")
    return ok({"assigned": True})


@router.delete("/admins/{uid}")
def revoke_admin(uid: int, request: Request, ctx: AdminContext = Depends(require("admins.manage")), db: Session = Depends(get_db)):
    if uid == ctx.user.id:
        raise ApiError(400, "self_action", "You cannot remove your own admin role.")
    a = db.scalar(select(AdminUser).where(AdminUser.user_id == uid))
    if not a:
        raise not_found("Administrator")
    a.is_active = False
    audit(db, ctx.user.id, "admin.revoked", "user", uid, request)
    db.commit()
    return ok({"revoked": True})


@router.get("/audit-logs")
def audit_logs(
    action: str | None = Query(None, max_length=80),
    page: int = 1,
    page_size: int = 50,
    ctx: AdminContext = Depends(require("audit.view")),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(like_term(action)))
    return paginate(
        db,
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()),
        page,
        page_size,
        lambda a: {
            "id": a.id,
            "actor": a.actor.full_name if a.actor else "System / anonymous",
            "action": a.action,
            "target_type": a.target_type,
            "target_id": a.target_id,
            "ip_address": a.ip_address,
            "meta": a.meta,
            "created_at": ser.iso(a.created_at),
        },
    )


@router.post("/uploads", status_code=201)
async def upload(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Query("content", pattern="^(content|records|news|events|councils|documents)$"),
    ctx: AdminContext = Depends(require("uploads.create")),
    db: Session = Depends(get_db),
):
    data = await file.read()
    stored = store_upload(data, folder)
    audit(db, ctx.user.id, "upload.created", None, None, request, url=stored["url"], size=stored["size"])
    db.commit()
    return ok(stored)


@router.get("/contact-messages")
def contact_messages(page: int = 1, page_size: int = 20, ctx: AdminContext = Depends(require("members.view")), db: Session = Depends(get_db)):
    return paginate(
        db,
        select(ContactMessage).order_by(ContactMessage.created_at.desc()),
        page,
        page_size,
        lambda m: {"id": m.id, "name": m.name, "email": m.email, "subject": m.subject, "message": m.message, "status": m.status, "created_at": ser.iso(m.created_at)},
    )
