from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from .. import serializers as ser
from ..database import get_db
from ..deps import csrf_protect, get_current_user
from ..errors import not_found
from ..models import Notification, User, utcnow
from ..responses import ok, paginate

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    unread: bool = False,
    type: str | None = Query(None, pattern="^(announcement|event|community|account|council_update)$"),
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread:
        stmt = stmt.where(Notification.read_at.is_(None))
    if type:
        stmt = stmt.where(Notification.type == type)
    result = paginate(db, stmt.order_by(Notification.created_at.desc(), Notification.id.desc()), page, page_size, ser.notification)
    result["meta"]["unread"] = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )
    return result


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )
    return ok({"unread": n or 0})


@router.post("/{nid}/read", dependencies=[Depends(csrf_protect)])
def mark_read(nid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.get(Notification, nid)
    if not n or n.user_id != user.id:
        raise not_found("Notification")
    n.read_at = n.read_at or utcnow()
    db.commit()
    return ok(ser.notification(n))


@router.post("/read-all", dependencies=[Depends(csrf_protect)])
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=utcnow())
    )
    db.commit()
    return ok({"unread": 0})
