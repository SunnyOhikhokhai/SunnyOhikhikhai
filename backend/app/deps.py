from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .errors import ApiError, forbidden
from .models import AdminUser, User, UserSession, utcnow
from .security import SESSION_COOKIE, check_csrf, token_digest


def _session_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return request.cookies.get(SESSION_COOKIE)


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = _session_token(request)
    if not token:
        return None
    sess = db.scalar(select(UserSession).where(UserSession.token_hash == token_digest(token)))
    now = utcnow()
    if not sess or sess.revoked_at or sess.expires_at <= now:
        return None
    user = db.get(User, sess.user_id)
    if not user or user.deleted_at or user.status != "active":
        return None
    if not user.last_seen_at or now - user.last_seen_at > timedelta(minutes=30):
        user.last_seen_at = now
        db.commit()
    request.state.session_id = sess.id
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if not user:
        raise ApiError(401, "unauthenticated", "Please log in to continue.")
    return user


def get_verified_user(user: User = Depends(get_current_user)) -> User:
    if not user.email_verified_at:
        raise ApiError(403, "verification_required", "Please verify your email address first.")
    return user


def csrf_protect(request: Request) -> None:
    check_csrf(request)


@dataclass
class AdminContext:
    user: User
    admin: AdminUser
    permissions: set[str]

    @property
    def role(self) -> str:
        return self.admin.role.code

    @property
    def scoped_council_id(self) -> int | None:
        """Area Council admins are restricted to their assigned council."""
        return self.admin.area_council_id if self.admin.role.is_scoped else None

    def has(self, perm: str) -> bool:
        return perm in self.permissions

    def ensure_council(self, area_council_id: int | None) -> None:
        scoped = self.scoped_council_id
        if self.admin.role.is_scoped and (scoped is None or area_council_id != scoped):
            raise forbidden("You can only manage content for your assigned Area Council.")


def get_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AdminContext:
    admin = db.scalar(select(AdminUser).where(AdminUser.user_id == user.id, AdminUser.is_active.is_(True)))
    if not admin:
        raise forbidden("Administrator access required.")
    return AdminContext(user=user, admin=admin, permissions={p.code for p in admin.role.permissions})


def require(*perms: str):
    def dependency(ctx: AdminContext = Depends(get_admin)) -> AdminContext:
        if not any(ctx.has(p) for p in perms):
            raise forbidden()
        return ctx

    return dependency
