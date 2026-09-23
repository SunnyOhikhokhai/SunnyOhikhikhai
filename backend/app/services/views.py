from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ContentViewStat, utcnow


def record_view(db: Session, obj, content_type: str) -> None:
    """Increment aggregate counters only; no per-user activity is stored."""
    obj.view_count = (obj.view_count or 0) + 1
    today = utcnow().date()
    stat = db.scalar(
        select(ContentViewStat).where(
            ContentViewStat.content_type == content_type,
            ContentViewStat.content_id == obj.id,
            ContentViewStat.day == today,
        )
    )
    if stat:
        stat.views += 1
    else:
        db.add(ContentViewStat(content_type=content_type, content_id=obj.id, day=today, views=1))
    db.commit()
