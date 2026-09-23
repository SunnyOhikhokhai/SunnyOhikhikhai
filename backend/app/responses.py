"""Consistent JSON envelopes: {"data": ...} and {"data": [...], "meta": {...}}."""

import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select


def ok(data: Any = None, **meta: Any) -> dict:
    body: dict = {"data": data}
    if meta:
        body["meta"] = meta
    return body


def paginate(db: Session, stmt: Select, page: int, page_size: int, serializer) -> dict:
    page = max(page, 1)
    page_size = max(1, min(page_size, 100))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).unique().all()
    return ok(
        [serializer(r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
    )
