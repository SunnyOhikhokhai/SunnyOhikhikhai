"""Public content: Area Councils, Our Record, News, Events, Announcements."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, extract, func, or_, select
from sqlalchemy.orm import Session

from .. import serializers as ser
from ..database import get_db
from ..deps import csrf_protect, get_optional_user, get_verified_user
from ..errors import ApiError, not_found
from ..models import (
    Announcement,
    AreaCouncil,
    Discussion,
    ElectionRecord,
    Event,
    EventRegistration,
    LegislativeRecord,
    MemberAreaCouncil,
    News,
    NewsCategory,
    Project,
    ProjectCategory,
    User,
    utcnow,
)
from ..responses import ok, paginate
from ..security import rate_limit
from ..services.views import record_view
from ..utils import like_term

router = APIRouter(prefix="/api", tags=["content"])


def _council_by_slug(db: Session, slug: str | None) -> AreaCouncil | None:
    if not slug:
        return None
    c = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == slug))
    if not c:
        raise not_found("Area Council")
    return c


def published_projects():
    return select(Project).where(Project.status == "published", Project.deleted_at.is_(None))


def published_news():
    return select(News).where(
        News.status == "published", News.deleted_at.is_(None), News.published_at <= utcnow()
    )


def published_legislation():
    return select(LegislativeRecord).where(LegislativeRecord.status == "published", LegislativeRecord.deleted_at.is_(None))


def published_elections():
    return select(ElectionRecord).where(ElectionRecord.status == "published", ElectionRecord.deleted_at.is_(None))


def visible_events():
    return select(Event).where(Event.status.in_(["published", "cancelled"]), Event.deleted_at.is_(None))


def active_announcements():
    now = utcnow()
    return select(Announcement).where(
        Announcement.status == "published",
        or_(Announcement.publish_at.is_(None), Announcement.publish_at <= now),
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
    )


def member_counts(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(MemberAreaCouncil.area_council_id, func.count())
        .join(User, and_(User.id == MemberAreaCouncil.user_id, User.deleted_at.is_(None)))
        .group_by(MemberAreaCouncil.area_council_id)
    ).all()
    return {cid: n for cid, n in rows}


def registration_counts(db: Session, event_ids: list[int]) -> dict[int, int]:
    if not event_ids:
        return {}
    rows = db.execute(
        select(EventRegistration.event_id, func.count())
        .where(EventRegistration.event_id.in_(event_ids), EventRegistration.status == "registered")
        .group_by(EventRegistration.event_id)
    ).all()
    return {eid: n for eid, n in rows}


# --- Meta -------------------------------------------------------------------


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    """Lookup lists for filters and forms."""
    from ..models import DiscussionCategory

    return ok(
        {
            "area_councils": [
                ser.council_ref(c) for c in db.scalars(select(AreaCouncil).order_by(AreaCouncil.sort_order)).all()
            ],
            "project_categories": [
                {"slug": c.slug, "name": c.name}
                for c in db.scalars(select(ProjectCategory).order_by(ProjectCategory.sort_order)).all()
            ],
            "news_categories": [
                {"slug": c.slug, "name": c.name}
                for c in db.scalars(select(NewsCategory).order_by(NewsCategory.sort_order)).all()
            ],
            "discussion_categories": [
                {"slug": c.slug, "name": c.name, "description": c.description}
                for c in db.scalars(select(DiscussionCategory).order_by(DiscussionCategory.sort_order)).all()
            ],
            "record_years": sorted(
                {y for y in db.scalars(published_projects().with_only_columns(Project.year).distinct()).all() if y},
                reverse=True,
            ),
            "legislation_categories": sorted(
                set(db.scalars(published_legislation().with_only_columns(LegislativeRecord.category).distinct()).all())
            ),
            "legislation_years": sorted(
                {y for y in db.scalars(published_legislation().with_only_columns(LegislativeRecord.year).distinct()).all() if y},
                reverse=True,
            ),
            "news_months": sorted(
                {d.strftime("%Y-%m") for d in db.scalars(published_news().with_only_columns(News.published_at)).all() if d},
                reverse=True,
            ),
        }
    )


@router.get("/home")
def home(db: Session = Depends(get_db)):
    """Everything the landing page needs in one request."""
    featured = db.scalars(
        published_projects().order_by(Project.is_featured.desc(), Project.published_at.desc()).limit(6)
    ).unique().all()
    counts = member_counts(db)
    councils = db.scalars(select(AreaCouncil).order_by(AreaCouncil.sort_order)).all()
    latest_by_council = {}
    for c in councils:
        n = db.scalars(published_news().where(News.area_council_id == c.id).order_by(News.published_at.desc()).limit(1)).first()
        latest_by_council[c.id] = {"title": n.title, "slug": n.slug, "published_at": ser.iso(n.published_at)} if n else None
    news = db.scalars(published_news().order_by(News.published_at.desc()).limit(3)).unique().all()
    events = db.scalars(
        visible_events().where(Event.status == "published", Event.starts_at >= utcnow()).order_by(Event.starts_at).limit(3)
    ).unique().all()
    discussions = db.scalars(
        select(Discussion)
        .where(Discussion.status == "visible", Discussion.deleted_at.is_(None))
        .order_by(Discussion.is_pinned.desc(), Discussion.last_activity_at.desc())
        .limit(3)
    ).unique().all()
    announcements = db.scalars(
        active_announcements().where(Announcement.area_council_id.is_(None)).order_by(Announcement.created_at.desc()).limit(2)
    ).unique().all()
    total_members = db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None))) or 0
    from .admin import get_profile

    profile = ser.principal(get_profile(db))
    current = db.scalars(published_elections().where(ElectionRecord.is_current.is_(True)).order_by(ElectionRecord.year.desc())).first()
    return ok(
        {
            "profile": {
                k: profile[k]
                for k in ("name", "title", "tagline", "summary", "photo_url", "photo_alt", "badges", "metrics", "metrics_note", "metrics_source_url")
            },
            "election": ser.election(current, ser.linked_sources(db, "election", [current.id])[current.id]) if current else None,
            "legislation_count": db.scalar(select(func.count()).select_from(published_legislation().subquery())) or 0,
            "featured": [ser.project_card(p) for p in featured],
            "councils": [
                ser.council(c, member_count=counts.get(c.id, 0), latest_update=latest_by_council[c.id]) for c in councils
            ],
            "news": [ser.news_card(n) for n in news],
            "events": [ser.event_card(e) for e in events],
            "discussions": [ser.discussion(d) for d in discussions],
            "announcements": [ser.announcement(a) for a in announcements],
            "stats": {
                "members": total_members,
                "records": db.scalar(select(func.count()).select_from(published_projects().subquery())) or 0,
                "councils": len(councils),
            },
        }
    )


# --- Sen. Philip Aduda profile ------------------------------------------------


@router.get("/profile")
def principal_profile(db: Session = Depends(get_db)):
    from .admin import get_profile

    return ok(ser.principal(get_profile(db)))


# --- Area Councils -----------------------------------------------------------


@router.get("/area-councils")
def list_councils(db: Session = Depends(get_db)):
    counts = member_counts(db)
    councils = db.scalars(select(AreaCouncil).order_by(AreaCouncil.sort_order)).all()
    out = []
    for c in councils:
        latest = db.scalars(
            published_news().where(News.area_council_id == c.id).order_by(News.published_at.desc()).limit(1)
        ).first()
        out.append(
            ser.council(
                c,
                member_count=counts.get(c.id, 0),
                latest_update={"title": latest.title, "slug": latest.slug, "published_at": ser.iso(latest.published_at)}
                if latest
                else None,
            )
        )
    return ok(out)


@router.get("/area-councils/{slug}")
def council_detail(slug: str, db: Session = Depends(get_db)):
    c = _council_by_slug(db, slug)
    now = utcnow()
    updates = db.scalars(published_news().where(News.area_council_id == c.id).order_by(News.published_at.desc()).limit(6)).unique().all()
    events = db.scalars(
        visible_events().where(Event.area_council_id == c.id, Event.starts_at >= now - timedelta(days=1)).order_by(Event.starts_at).limit(6)
    ).unique().all()
    records = db.scalars(published_projects().where(Project.area_council_id == c.id).order_by(Project.published_at.desc()).limit(6)).unique().all()
    discussions = db.scalars(
        select(Discussion)
        .where(Discussion.area_council_id == c.id, Discussion.status == "visible", Discussion.deleted_at.is_(None))
        .order_by(Discussion.last_activity_at.desc())
        .limit(6)
    ).unique().all()
    announcements = db.scalars(
        active_announcements().where(Announcement.area_council_id == c.id).order_by(Announcement.created_at.desc()).limit(6)
    ).unique().all()
    info = db.scalars(
        published_news()
        .join(NewsCategory)
        .where(News.area_council_id == c.id, NewsCategory.slug == "public-information")
        .order_by(News.published_at.desc())
        .limit(6)
    ).unique().all()
    return ok(
        {
            "council": ser.council(c, member_count=member_counts(db).get(c.id, 0)),
            "updates": [ser.news_card(n) for n in updates],
            "public_information": [ser.news_card(n) for n in info],
            "events": [ser.event_card(e) for e in events],
            "records": [ser.project_card(p) for p in records],
            "discussions": [ser.discussion(d) for d in discussions],
            "announcements": [ser.announcement(a) for a in announcements],
        }
    )


# --- Our Record ----------------------------------------------------------------


@router.get("/projects")
def list_projects(
    q: str | None = Query(None, max_length=100),
    area_council: str | None = None,
    category: str | None = None,
    year: int | None = None,
    verification: str | None = None,
    project_status: str | None = None,
    featured: bool | None = None,
    sort: str = Query("recent", pattern="^(recent|oldest|year_desc|year_asc|title|popular)$"),
    page: int = 1,
    page_size: int = 12,
    db: Session = Depends(get_db),
):
    stmt = published_projects()
    if q:
        t = like_term(q)
        stmt = stmt.where(
            or_(
                Project.title.ilike(t),
                Project.summary.ilike(t),
                Project.location.ilike(t),
                Project.category_label.ilike(t),
            )
        )
    if project_status:
        stmt = stmt.where(Project.project_status == project_status)
    if area_council:
        stmt = stmt.where(Project.area_council_id == _council_by_slug(db, area_council).id)
    if category:
        stmt = stmt.join(ProjectCategory).where(ProjectCategory.slug == category)
    if year:
        stmt = stmt.where(Project.year == year)
    if verification:
        stmt = stmt.where(Project.verification_status == verification)
    if featured is not None:
        stmt = stmt.where(Project.is_featured.is_(featured))
    order = {
        "recent": Project.published_at.desc(),
        "oldest": Project.published_at.asc(),
        "year_desc": Project.year.desc(),
        "year_asc": Project.year.asc(),
        "title": Project.title.asc(),
        "popular": Project.view_count.desc(),
    }[sort]
    return paginate(db, stmt.order_by(order, Project.id.desc()), page, page_size, ser.project_card)


@router.get("/projects/{slug}")
def project_detail(slug: str, db: Session = Depends(get_db)):
    p = db.scalars(published_projects().where(Project.slug == slug)).first()
    if not p:
        raise not_found("Record")
    record_view(db, p, "project")
    related_stmt = published_projects().where(Project.id != p.id)
    related_stmt = related_stmt.where(
        or_(Project.category_id == p.category_id, Project.area_council_id == p.area_council_id)
    )
    related = db.scalars(related_stmt.order_by(Project.published_at.desc()).limit(3)).unique().all()
    return ok({**ser.project_detail(p), "related": [ser.project_card(r) for r in related]})


# --- News ----------------------------------------------------------------------


@router.get("/news")
def list_news(
    q: str | None = Query(None, max_length=100),
    category: str | None = None,
    area_council: str | None = None,
    month: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    verification: str | None = None,
    page: int = 1,
    page_size: int = 9,
    db: Session = Depends(get_db),
):
    stmt = published_news()
    if q:
        t = like_term(q)
        stmt = stmt.where(or_(News.title.ilike(t), News.excerpt.ilike(t)))
    if month:
        y, m = (int(x) for x in month.split("-"))
        stmt = stmt.where(extract("year", News.published_at) == y, extract("month", News.published_at) == m)
    if verification:
        stmt = stmt.where(News.verification_status == verification)
    if category:
        stmt = stmt.join(NewsCategory).where(NewsCategory.slug == category)
    if area_council:
        stmt = stmt.where(News.area_council_id == _council_by_slug(db, area_council).id)
    return paginate(db, stmt.order_by(News.published_at.desc(), News.id.desc()), page, page_size, ser.news_card)


@router.get("/news/{slug}")
def news_detail(slug: str, db: Session = Depends(get_db)):
    n = db.scalars(published_news().where(News.slug == slug)).first()
    if not n:
        raise not_found("Article")
    record_view(db, n, "news")
    related = db.scalars(
        published_news().where(News.id != n.id, News.category_id == n.category_id).order_by(News.published_at.desc()).limit(3)
    ).unique().all()
    sources = ser.linked_sources(db, "news", [n.id])[n.id]
    return ok({**ser.news_detail(n, sources), "related": [ser.news_card(r) for r in related]})


# --- Legislation and elections ---------------------------------------------------


def _with_sources(db: Session, content_type: str, items: list, fn) -> list[dict]:
    src = ser.linked_sources(db, content_type, [i.id for i in items])
    return [fn(i, src[i.id]) for i in items]


@router.get("/legislation")
def list_legislation(
    q: str | None = Query(None, max_length=100),
    category: str | None = Query(None, max_length=80),
    year: int | None = None,
    stage: str | None = None,
    verification: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    stmt = published_legislation()
    if q:
        t = like_term(q)
        stmt = stmt.where(
            or_(
                LegislativeRecord.title.ilike(t),
                LegislativeRecord.description.ilike(t),
                LegislativeRecord.bill_number.ilike(t),
                LegislativeRecord.category.ilike(t),
            )
        )
    if category:
        stmt = stmt.where(LegislativeRecord.category == category)
    if year:
        stmt = stmt.where(LegislativeRecord.year == year)
    if stage:
        stmt = stmt.where(LegislativeRecord.legislative_stage == stage)
    if verification:
        stmt = stmt.where(LegislativeRecord.verification_status == verification)
    stmt = stmt.order_by(LegislativeRecord.is_featured.desc(), LegislativeRecord.year.desc().nulls_last(), LegislativeRecord.title)
    page = max(1, page)
    page_size = min(max(1, page_size), 50)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return ok(
        _with_sources(db, "legislation", rows, ser.legislation),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, -(-total // page_size)),
    )


@router.get("/legislation/{slug}")
def legislation_detail(slug: str, db: Session = Depends(get_db)):
    r = db.scalars(published_legislation().where(LegislativeRecord.slug == slug)).first()
    if not r:
        raise not_found("Legislative record")
    related = db.scalars(
        published_legislation().where(LegislativeRecord.id != r.id, LegislativeRecord.category == r.category).limit(3)
    ).all()
    return ok(
        {
            **ser.legislation(r, ser.linked_sources(db, "legislation", [r.id])[r.id]),
            "related": _with_sources(db, "legislation", related, ser.legislation),
        }
    )


@router.get("/elections")
def list_elections(db: Session = Depends(get_db)):
    rows = db.scalars(published_elections().order_by(ElectionRecord.year.desc(), ElectionRecord.id.desc())).all()
    return ok(_with_sources(db, "election", rows, ser.election))


# --- Events --------------------------------------------------------------------


@router.get("/events")
def list_events(
    when: str = Query("upcoming", pattern="^(upcoming|past|all)$"),
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    area_council: str | None = None,
    q: str | None = Query(None, max_length=100),
    page: int = 1,
    page_size: int = 12,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    now = utcnow()
    stmt = visible_events()
    order = Event.starts_at.asc()
    if month:
        y, m = map(int, month.split("-"))
        stmt = stmt.where(extract("year", Event.starts_at) == y, extract("month", Event.starts_at) == m)
        page_size = 100
    elif when == "upcoming":
        stmt = stmt.where(Event.starts_at >= now - timedelta(hours=6))
    elif when == "past":
        stmt = stmt.where(Event.starts_at < now)
        order = Event.starts_at.desc()
    if area_council:
        stmt = stmt.where(Event.area_council_id == _council_by_slug(db, area_council).id)
    if q:
        t = like_term(q)
        stmt = stmt.where(or_(Event.title.ilike(t), Event.location.ilike(t)))
    result = paginate(db, stmt.order_by(order), page, page_size, lambda e: e)
    events = result["data"]
    counts = registration_counts(db, [e.id for e in events])
    mine = set()
    if user:
        mine = set(
            db.scalars(
                select(EventRegistration.event_id).where(
                    EventRegistration.user_id == user.id, EventRegistration.status == "registered"
                )
            ).all()
        )
    result["data"] = [
        ser.event_card(e, registered_count=counts.get(e.id, 0), is_registered=(e.id in mine) if user else None)
        for e in events
    ]
    return result


def _event_or_404(db: Session, slug_or_id: str) -> Event:
    cond = Event.id == int(slug_or_id) if slug_or_id.isdigit() else Event.slug == slug_or_id
    e = db.scalars(visible_events().where(cond)).first()
    if not e:
        raise not_found("Event")
    return e


@router.get("/events/{slug}")
def event_detail(slug: str, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    e = _event_or_404(db, slug)
    record_view(db, e, "event")
    count = registration_counts(db, [e.id]).get(e.id, 0)
    is_reg = None
    if user:
        is_reg = bool(
            db.scalar(
                select(EventRegistration.id).where(
                    EventRegistration.event_id == e.id,
                    EventRegistration.user_id == user.id,
                    EventRegistration.status == "registered",
                )
            )
        )
    return ok(ser.event_detail(e, registered_count=count, is_registered=is_reg))


@router.post("/events/{slug}/register", dependencies=[Depends(csrf_protect), Depends(rate_limit("event-reg", 20, 60))])
def register_for_event(slug: str, db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    e = _event_or_404(db, slug)
    if e.status != "published" or not e.registration_open or e.starts_at < utcnow():
        raise ApiError(400, "registration_closed", "Registration for this event is closed.")
    reg = db.scalar(select(EventRegistration).where(EventRegistration.event_id == e.id, EventRegistration.user_id == user.id))
    if reg and reg.status == "registered":
        return ok({"registered": True})
    count = registration_counts(db, [e.id]).get(e.id, 0)
    if e.capacity is not None and count >= e.capacity:
        raise ApiError(409, "event_full", "This event is fully booked.")
    if reg:
        reg.status = "registered"
        reg.created_at = utcnow()
    else:
        db.add(EventRegistration(event_id=e.id, user_id=user.id))
    from ..services.notify import notify_users

    db.commit()
    notify_users(db, [user], "account", f"You're registered: {e.title}", f"{e.location}", f"/events/{e.slug}")
    return ok({"registered": True})


@router.delete("/events/{slug}/register", dependencies=[Depends(csrf_protect)])
def cancel_registration(slug: str, db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    e = _event_or_404(db, slug)
    reg = db.scalar(select(EventRegistration).where(EventRegistration.event_id == e.id, EventRegistration.user_id == user.id))
    if reg:
        reg.status = "cancelled"
        db.commit()
    return ok({"registered": False})


@router.get("/members/events")
def my_events(db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    rows = db.scalars(
        select(Event)
        .join(EventRegistration, EventRegistration.event_id == Event.id)
        .where(EventRegistration.user_id == user.id, EventRegistration.status == "registered", Event.deleted_at.is_(None))
        .order_by(Event.starts_at.desc())
    ).unique().all()
    return ok([ser.event_card(e, is_registered=True) for e in rows])


# --- Announcements -------------------------------------------------------------


@router.get("/announcements")
def list_announcements(area_council: str | None = None, db: Session = Depends(get_db)):
    stmt = active_announcements()
    if area_council:
        stmt = stmt.where(Announcement.area_council_id == _council_by_slug(db, area_council).id)
    else:
        stmt = stmt.where(Announcement.area_council_id.is_(None))
    rows = db.scalars(stmt.order_by(case((Announcement.priority == "important", 0), else_=1), Announcement.created_at.desc()).limit(10)).unique().all()
    return ok([ser.announcement(a) for a in rows])

