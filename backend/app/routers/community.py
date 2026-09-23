"""Moderated community: discussions, comments, reactions and reports."""

from __future__ import annotations

import re
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import serializers as ser
from ..database import get_db
from ..deps import csrf_protect, get_optional_user, get_verified_user
from ..errors import ApiError, forbidden, not_found
from ..models import (
    AreaCouncil,
    Comment,
    Discussion,
    DiscussionCategory,
    Reaction,
    Report,
    User,
    utcnow,
)
from ..responses import ok, paginate
from ..schemas import CommentIn, DiscussionIn, ReportIn
from ..security import rate_limit
from ..services.audit import audit
from ..services.notify import notify_users
from ..utils import like_term

router = APIRouter(prefix="/api", tags=["community"])

URL_RE = re.compile(r"https?://", re.I)
PHONE_RE = re.compile(r"(?:\+?234|0)[789][01]\d[\s-]?\d{3}[\s-]?\d{4}")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def check_content(db: Session, user: User, text: str, model, body: str | None = None) -> None:
    """Anti-spam and personal-information safeguards."""
    if len(URL_RE.findall(text)) > 3:
        raise ApiError(422, "too_many_links", "Posts may contain at most 3 links.")
    if PHONE_RE.search(text) or EMAIL_RE.search(text):
        raise ApiError(
            422,
            "personal_information",
            "For everyone's safety, please don't post phone numbers or email addresses in the community.",
        )
    if user.created_at > utcnow() - timedelta(minutes=2) and URL_RE.search(text):
        raise ApiError(422, "new_account_links", "New accounts can post links after a few minutes.")
    dup = db.scalar(
        select(model.id).where(
            model.author_id == user.id,
            model.body == (body if body is not None else text), model.created_at > utcnow() - timedelta(minutes=10)
        )
    )
    if dup:
        raise ApiError(409, "duplicate_post", "You've already posted this. Please avoid repeating content.")


def _liked(db: Session, user: User | None, target_type: str, ids: list[int]) -> set[int]:
    if not user or not ids:
        return set()
    return set(
        db.scalars(
            select(Reaction.target_id).where(
                Reaction.user_id == user.id, Reaction.target_type == target_type, Reaction.target_id.in_(ids)
            )
        ).all()
    )


def _discussion_or_404(db: Session, did: int) -> Discussion:
    d = db.get(Discussion, did)
    if not d or d.deleted_at or d.status == "removed":
        raise not_found("Discussion")
    return d


@router.get("/discussions")
def list_discussions(
    q: str | None = Query(None, max_length=100),
    category: str | None = None,
    area_council: str | None = None,
    sort: str = Query("active", pattern="^(active|new|popular)$"),
    page: int = 1,
    page_size: int = 15,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    stmt = select(Discussion).where(Discussion.status == "visible", Discussion.deleted_at.is_(None))
    if q:
        t = like_term(q)
        stmt = stmt.where(or_(Discussion.title.ilike(t), Discussion.body.ilike(t)))
    if category:
        stmt = stmt.join(DiscussionCategory).where(DiscussionCategory.slug == category)
    if area_council:
        stmt = stmt.join(AreaCouncil, AreaCouncil.id == Discussion.area_council_id).where(AreaCouncil.slug == area_council)
    order = {
        "active": Discussion.last_activity_at.desc(),
        "new": Discussion.created_at.desc(),
        "popular": (Discussion.reaction_count + Discussion.comment_count).desc(),
    }[sort]
    result = paginate(db, stmt.order_by(Discussion.is_pinned.desc(), order), page, page_size, lambda d: d)
    liked = _liked(db, user, "discussion", [d.id for d in result["data"]])
    result["data"] = [ser.discussion(d, liked=(d.id in liked) if user else None) for d in result["data"]]
    return result


@router.post(
    "/discussions",
    status_code=201,
    dependencies=[Depends(csrf_protect), Depends(rate_limit("discussion-create", 5, 600))],
)
def create_discussion(body: DiscussionIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    cat = db.scalar(select(DiscussionCategory).where(DiscussionCategory.slug == body.category))
    if not cat:
        raise ApiError(422, "invalid_category", "Choose a valid discussion category.")
    council = None
    if body.area_council:
        council = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == body.area_council))
        if not council:
            raise ApiError(422, "invalid_area_council", "Choose a valid Area Council.")
    check_content(db, user, body.title + "\n" + body.body, Discussion, body.body)
    d = Discussion(
        title=body.title,
        body=body.body,
        category_id=cat.id,
        area_council_id=council.id if council else None,
        author_id=user.id,
    )
    db.add(d)
    db.flush()
    audit(db, user.id, "community.discussion_created", "discussion", d.id, request)
    db.commit()
    return ok(ser.discussion(d, liked=False))


@router.get("/discussions/{did}")
def get_discussion(did: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    d = _discussion_or_404(db, did)
    if d.status == "hidden":
        raise not_found("Discussion")
    comments = db.scalars(
        select(Comment).where(Comment.discussion_id == d.id).order_by(Comment.created_at.asc())
    ).unique().all()
    liked_d = _liked(db, user, "discussion", [d.id])
    liked_c = _liked(db, user, "comment", [c.id for c in comments])
    return ok(
        {
            **ser.discussion(d, liked=(d.id in liked_d) if user else None),
            "can_edit": bool(user and user.id == d.author_id),
            "comments": [ser.comment(c, liked=(c.id in liked_c) if user else None) for c in comments],
        }
    )


@router.delete("/discussions/{did}", dependencies=[Depends(csrf_protect)])
def delete_discussion(did: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    d = _discussion_or_404(db, did)
    if d.author_id != user.id:
        raise forbidden("You can only delete your own discussions.")
    d.deleted_at = utcnow()
    audit(db, user.id, "community.discussion_deleted", "discussion", d.id, request)
    db.commit()
    return ok({"deleted": True})


@router.post(
    "/discussions/{did}/comments",
    status_code=201,
    dependencies=[Depends(csrf_protect), Depends(rate_limit("comment-create", 20, 600))],
)
def add_comment(
    did: int,
    body: CommentIn,
    request: Request,
    tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_verified_user),
):
    d = _discussion_or_404(db, did)
    if d.is_locked or d.status != "visible":
        raise ApiError(403, "discussion_locked", "This discussion is closed to new comments.")
    parent = None
    if body.parent_id:
        parent = db.get(Comment, body.parent_id)
        if not parent or parent.discussion_id != d.id:
            raise ApiError(422, "invalid_parent", "You can only reply to comments in this discussion.")
        if parent.parent_id:  # keep threads one level deep
            parent = db.get(Comment, parent.parent_id)
    check_content(db, user, body.body, Comment)
    c = Comment(discussion_id=d.id, parent_id=parent.id if parent else None, author_id=user.id, body=body.body)
    db.add(c)
    d.comment_count = (d.comment_count or 0) + 1
    d.last_activity_at = utcnow()
    db.flush()
    audit(db, user.id, "community.comment_created", "comment", c.id, request)
    db.commit()
    recipients = {d.author_id} | ({parent.author_id} if parent else set())
    recipients.discard(user.id)
    if recipients:
        users = list(db.scalars(select(User).where(User.id.in_(recipients), User.deleted_at.is_(None))).all())
        notify_users(
            db,
            users,
            "community",
            f"New reply in “{d.title[:80]}”",
            f"{ser.public_author(user)['name']} replied.",
            f"/community/{d.id}",
            tasks,
        )
    return ok(ser.comment(c, liked=False))


@router.delete("/comments/{cid}", dependencies=[Depends(csrf_protect)])
def delete_comment(cid: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    c = db.get(Comment, cid)
    if not c or c.deleted_at:
        raise not_found("Comment")
    if c.author_id != user.id:
        raise forbidden("You can only delete your own comments.")
    c.deleted_at = utcnow()
    d = db.get(Discussion, c.discussion_id)
    if d:
        d.comment_count = max(0, (d.comment_count or 0) - 1)
    audit(db, user.id, "community.comment_deleted", "comment", c.id, request)
    db.commit()
    return ok({"deleted": True})


@router.post("/reactions", dependencies=[Depends(csrf_protect), Depends(rate_limit("react", 60, 60))])
def toggle_reaction(
    target_type: str = Query(pattern="^(discussion|comment)$"),
    target_id: int = Query(),
    db: Session = Depends(get_db),
    user: User = Depends(get_verified_user),
):
    model = Discussion if target_type == "discussion" else Comment
    target = db.get(model, target_id)
    if not target or target.deleted_at or target.status != "visible":
        raise not_found("Content")
    existing = db.scalar(
        select(Reaction).where(
            Reaction.user_id == user.id, Reaction.target_type == target_type, Reaction.target_id == target_id
        )
    )
    if existing:
        db.delete(existing)
        target.reaction_count = max(0, (target.reaction_count or 0) - 1)
        liked = False
    else:
        db.add(Reaction(user_id=user.id, target_type=target_type, target_id=target_id))
        target.reaction_count = (target.reaction_count or 0) + 1
        liked = True
    db.commit()
    return ok({"liked": liked, "reaction_count": target.reaction_count})


@router.post(
    "/reports", status_code=201, dependencies=[Depends(csrf_protect), Depends(rate_limit("report", 10, 600))]
)
def create_report(body: ReportIn, request: Request, db: Session = Depends(get_db), user: User = Depends(get_verified_user)):
    model = Discussion if body.target_type == "discussion" else Comment
    target = db.get(model, body.target_id)
    if not target or target.deleted_at:
        raise not_found("Content")
    already = db.scalar(
        select(Report.id).where(
            Report.reporter_id == user.id,
            Report.target_type == body.target_type,
            Report.target_id == body.target_id,
            Report.status == "open",
        )
    )
    if not already:
        r = Report(reporter_id=user.id, target_type=body.target_type, target_id=body.target_id, reason=body.reason, details=body.details)
        db.add(r)
        db.flush()
        audit(db, user.id, "community.reported", body.target_type, body.target_id, request, reason=body.reason)
        # Auto-hide content that attracts several independent reports pending review.
        open_reports = db.scalar(
            select(func.count(func.distinct(Report.reporter_id))).where(
                Report.target_type == body.target_type, Report.target_id == body.target_id, Report.status == "open"
            )
        )
        if open_reports and open_reports >= 3 and target.status == "visible":
            target.status = "hidden"
        db.commit()
    return ok({"reported": True, "message": "Thank you. Our moderators will review this report."})
