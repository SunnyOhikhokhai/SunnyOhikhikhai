"""Global search, contact form, sitemap."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import serializers as ser
from ..config import get_settings
from ..database import get_db
from ..deps import csrf_protect
from ..models import AreaCouncil, ContactMessage, Discussion, Event, News, Project
from ..responses import ok
from ..schemas import ContactIn
from ..security import rate_limit
from ..services.audit import audit
from ..utils import like_term
from .content import published_news, published_projects, visible_events

router = APIRouter(tags=["public"])


@router.get("/api/search")
def search(
    q: str = Query(min_length=2, max_length=100),
    type: str | None = Query(None, pattern="^(records|news|events|councils|discussions)$"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    _rl: None = Depends(rate_limit("search", 60, 60)),
):
    t = like_term(q)
    out: dict[str, list] = {}
    if type in (None, "records"):
        out["records"] = [
            ser.project_card(p)
            for p in db.scalars(
                published_projects()
                .where(or_(Project.title.ilike(t), Project.summary.ilike(t), Project.location.ilike(t), Project.description.ilike(t)))
                .order_by(Project.published_at.desc())
                .limit(limit)
            ).unique()
        ]
    if type in (None, "news"):
        out["news"] = [
            ser.news_card(n)
            for n in db.scalars(
                published_news()
                .where(or_(News.title.ilike(t), News.excerpt.ilike(t), News.body.ilike(t)))
                .order_by(News.published_at.desc())
                .limit(limit)
            ).unique()
        ]
    if type in (None, "events"):
        out["events"] = [
            ser.event_card(e)
            for e in db.scalars(
                visible_events()
                .where(or_(Event.title.ilike(t), Event.location.ilike(t), Event.summary.ilike(t)))
                .order_by(Event.starts_at.desc())
                .limit(limit)
            ).unique()
        ]
    if type in (None, "councils"):
        out["councils"] = [
            ser.council_ref(c)
            for c in db.scalars(
                select(AreaCouncil).where(
                    or_(AreaCouncil.name.ilike(t), AreaCouncil.short_name.ilike(t), AreaCouncil.summary.ilike(t))
                )
            )
        ]
    if type in (None, "discussions"):
        out["discussions"] = [
            ser.discussion(d)
            for d in db.scalars(
                select(Discussion)
                .where(
                    Discussion.status == "visible",
                    Discussion.deleted_at.is_(None),
                    or_(Discussion.title.ilike(t), Discussion.body.ilike(t)),
                )
                .order_by(Discussion.last_activity_at.desc())
                .limit(limit)
            ).unique()
        ]
    return ok(out, query=q, total=sum(len(v) for v in out.values()))


@router.post("/api/contact", status_code=201, dependencies=[Depends(csrf_protect), Depends(rate_limit("contact", 3, 600))])
def contact(body: ContactIn, request: Request, db: Session = Depends(get_db)):
    m = ContactMessage(name=body.name, email=body.email, subject=body.subject, message=body.message)
    db.add(m)
    db.flush()
    audit(db, None, "contact.received", "contact_message", m.id, request)
    db.commit()
    return ok({"received": True})


STATIC_PATHS = [
    "/", "/about", "/our-record", "/area-councils", "/news", "/events", "/community", "/contact",
    "/join", "/privacy", "/terms", "/community-guidelines",
]


@router.get("/sitemap.xml", include_in_schema=False)
@router.get("/api/sitemap.xml", include_in_schema=False)
def sitemap(db: Session = Depends(get_db)):
    base = get_settings().public_base_url.rstrip("/")
    urls = [f"{base}{p}" for p in STATIC_PATHS]
    urls += [f"{base}/area-councils/{s}" for s in db.scalars(select(AreaCouncil.slug)).all()]
    urls += [f"{base}/our-record/{p.slug}" for p in db.scalars(published_projects()).unique()]
    urls += [f"{base}/news/{n.slug}" for n in db.scalars(published_news()).unique()]
    urls += [f"{base}/events/{e.slug}" for e in db.scalars(visible_events()).unique()]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body += "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    body += "</urlset>\n"
    return Response(body, media_type="application/xml")
