import re
import secrets
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session


def slugify(text: str, max_len: int = 120) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text[:max_len].strip("-")) or "item"


def unique_slug(db: Session, model, title: str, exclude_id: int | None = None) -> str:
    base = slugify(title)
    slug = base
    while True:
        stmt = select(model.id).where(model.slug == slug)
        if exclude_id:
            stmt = stmt.where(model.id != exclude_id)
        if not db.scalar(stmt):
            return slug
        slug = f"{base}-{secrets.token_hex(2)}"


def like_term(q: str) -> str:
    q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{q.strip()}%"
