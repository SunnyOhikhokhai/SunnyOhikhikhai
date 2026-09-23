"""Relational schema for the NIPAM platform.

Conventions:
- Integer surrogate primary keys, explicit foreign keys and indexes.
- ``created_at`` / ``updated_at`` timestamps on every mutable table.
- ``deleted_at`` soft deletion on user-facing content and accounts.
- ``is_demo`` marks sample content that is not verified information.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Timezone-aware datetimes on every backend (SQLite drops tzinfo)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), default=utcnow, onupdate=utcnow, nullable=False
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True, index=True)


# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------


class AreaCouncil(TimestampMixin, Base):
    __tablename__ = "area_councils"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    short_name: Mapped[str] = mapped_column(String(40))
    headquarters: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    wards: Mapped[list[Ward]] = relationship(back_populates="area_council", order_by="Ward.name")


class Ward(TimestampMixin, Base):
    __tablename__ = "wards"
    __table_args__ = (UniqueConstraint("area_council_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    area_council_id: Mapped[int] = mapped_column(ForeignKey("area_councils.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))

    area_council: Mapped[AreaCouncil] = relationship(back_populates="wards")


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # active | suspended
    suspended_reason: Mapped[str | None] = mapped_column(String(500))
    email_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    phone_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), index=True)

    profile: Mapped[Profile] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    council_link: Mapped[MemberAreaCouncil | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped[NotificationPreference] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin: Mapped[AdminUser | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", foreign_keys="AdminUser.user_id"
    )

    @property
    def first_name(self) -> str:
        return (self.full_name or "").split(" ")[0]

    @property
    def is_verified(self) -> bool:
        return self.email_verified_at is not None


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(80))
    bio: Mapped[str | None] = mapped_column(String(500))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    ward_id: Mapped[int | None] = mapped_column(ForeignKey("wards.id", ondelete="SET NULL"))
    ward_name: Mapped[str | None] = mapped_column(String(120))
    community: Mapped[str | None] = mapped_column(String(120))
    consent_recorded_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    terms_accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    user: Mapped[User] = relationship(back_populates="profile")


class MemberAreaCouncil(TimestampMixin, Base):
    """The Area Council a member says they reside in. Self-declared; not proof of
    electoral eligibility or voting location."""

    __tablename__ = "member_area_councils"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    area_council_id: Mapped[int] = mapped_column(ForeignKey("area_councils.id", ondelete="RESTRICT"), index=True)

    user: Mapped[User] = relationship(back_populates="council_link")
    area_council: Mapped[AreaCouncil] = relationship()


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(300))

    user: Mapped[User] = relationship()


class VerificationCode(Base):
    """One-time codes for email/phone verification, OTP login and password reset.
    Only a hash of the code is stored."""

    __tablename__ = "verification_codes"
    __table_args__ = (Index("ix_vcode_lookup", "user_id", "purpose", "channel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(30))  # verify_email | verify_phone | login | reset_password
    channel: Mapped[str] = mapped_column(String(10))  # email | sms
    code_hash: Mapped[str] = mapped_column(String(64))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    consumed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class NotificationPreference(TimestampMixin, Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    # Account/security messages are essential and always sent.
    in_app_announcements: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_events: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_community: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_council_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    email_announcements: Mapped[bool] = mapped_column(Boolean, default=False)
    email_events: Mapped[bool] = mapped_column(Boolean, default=False)
    email_community: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_announcements: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_events: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="preferences")


# ---------------------------------------------------------------------------
# Administration / RBAC
# ---------------------------------------------------------------------------

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    description: Mapped[str] = mapped_column(String(200), default="")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)  # super_admin, content_admin, ...
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300), default="")
    is_scoped: Mapped[bool] = mapped_column(Boolean, default=False)

    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions, lazy="selectin")


class AdminUser(TimestampMixin, Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    area_council_id: Mapped[int | None] = mapped_column(ForeignKey("area_councils.id", ondelete="SET NULL"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    user: Mapped[User] = relationship(back_populates="admin", foreign_keys=[user_id])
    role: Mapped[Role] = relationship(lazy="selectin")
    area_council: Mapped[AreaCouncil | None] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str | None] = mapped_column(String(40))
    target_id: Mapped[int | None] = mapped_column(Integer)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)

    actor: Mapped[User | None] = relationship()


# ---------------------------------------------------------------------------
# Our Record (projects / public records)
# ---------------------------------------------------------------------------


class ProjectCategory(Base):
    __tablename__ = "project_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Project(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_pub", "status", "published_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category_id: Mapped[int] = mapped_column(ForeignKey("project_categories.id", ondelete="RESTRICT"), index=True)
    area_council_id: Mapped[int | None] = mapped_column(ForeignKey("area_councils.id", ondelete="SET NULL"), index=True)
    location: Mapped[str | None] = mapped_column(String(200))
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    record_date: Mapped[date | None] = mapped_column(Date)
    summary: Mapped[str] = mapped_column(String(400), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # unverified | pending_review | verified | disputed
    verification_status: Mapped[str] = mapped_column(String(20), default="unverified", index=True)
    verification_note: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    category: Mapped[ProjectCategory] = relationship(lazy="joined")
    area_council: Mapped[AreaCouncil | None] = relationship(lazy="joined")
    sources: Mapped[list[ProjectSource]] = relationship(
        cascade="all, delete-orphan", order_by="ProjectSource.id", lazy="selectin"
    )
    images: Mapped[list[ProjectImage]] = relationship(
        cascade="all, delete-orphan", order_by="ProjectImage.sort_order", lazy="selectin"
    )
    documents: Mapped[list[ProjectDocument]] = relationship(
        cascade="all, delete-orphan", order_by="ProjectDocument.id", lazy="selectin"
    )


class ProjectSource(Base):
    __tablename__ = "project_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str | None] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(500))
    published_on: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(500))


class ProjectImage(Base):
    __tablename__ = "project_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    alt: Mapped[str] = mapped_column(String(300), default="")
    caption: Mapped[str | None] = mapped_column(String(300))
    credit: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(20))


# ---------------------------------------------------------------------------
# News & announcements
# ---------------------------------------------------------------------------


class NewsCategory(Base):
    __tablename__ = "news_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class News(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "news"
    __table_args__ = (Index("ix_news_pub", "status", "published_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    excerpt: Mapped[str] = mapped_column(String(400), default="")
    body: Mapped[str] = mapped_column(Text, default="")  # Markdown (raw HTML is not rendered)
    category_id: Mapped[int] = mapped_column(ForeignKey("news_categories.id", ondelete="RESTRICT"), index=True)
    area_council_id: Mapped[int | None] = mapped_column(ForeignKey("area_councils.id", ondelete="SET NULL"), index=True)
    # verified_information | announcement | opinion | historical_record | update
    content_label: Mapped[str] = mapped_column(String(30), default="update")
    source_note: Mapped[str | None] = mapped_column(String(400))
    image_url: Mapped[str | None] = mapped_column(String(500))
    image_alt: Mapped[str | None] = mapped_column(String(300))
    author_name: Mapped[str] = mapped_column(String(120), default="NIPAM Editorial Team")
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    category: Mapped[NewsCategory] = relationship(lazy="joined")
    area_council: Mapped[AreaCouncil | None] = relationship(lazy="joined")


class Announcement(TimestampMixin, Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    link_url: Mapped[str | None] = mapped_column(String(500))
    area_council_id: Mapped[int | None] = mapped_column(ForeignKey("area_councils.id", ondelete="SET NULL"), index=True)
    priority: Mapped[str] = mapped_column(String(10), default="normal")  # normal | important
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published
    publish_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    notified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    area_council: Mapped[AreaCouncil | None] = relationship(lazy="joined")


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class Event(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(String(400), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    location: Mapped[str] = mapped_column(String(200))
    area_council_id: Mapped[int | None] = mapped_column(ForeignKey("area_councils.id", ondelete="SET NULL"), index=True)
    image_url: Mapped[str | None] = mapped_column(String(500))
    organizer: Mapped[str] = mapped_column(String(160), default="NIPAM")
    registration_open: Mapped[bool] = mapped_column(Boolean, default=True)
    capacity: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | published | cancelled | archived
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    notified_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    area_council: Mapped[AreaCouncil | None] = relationship(lazy="joined")


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="registered")  # registered | cancelled
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)

    event: Mapped[Event] = relationship()


# ---------------------------------------------------------------------------
# Community
# ---------------------------------------------------------------------------


class DiscussionCategory(Base):
    __tablename__ = "discussion_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Discussion(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "discussions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(ForeignKey("discussion_categories.id", ondelete="RESTRICT"), index=True)
    area_council_id: Mapped[int | None] = mapped_column(ForeignKey("area_councils.id", ondelete="SET NULL"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="visible", index=True)  # visible | hidden | removed
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    reaction_count: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)

    category: Mapped[DiscussionCategory] = relationship(lazy="joined")
    area_council: Mapped[AreaCouncil | None] = relationship(lazy="joined")
    author: Mapped[User] = relationship(lazy="joined")


class Comment(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    discussion_id: Mapped[int] = mapped_column(ForeignKey("discussions.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="visible")  # visible | hidden | removed
    reaction_count: Mapped[int] = mapped_column(Integer, default=0)

    author: Mapped[User] = relationship(lazy="joined")


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint("user_id", "target_type", "target_id", "kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))  # discussion | comment
    target_id: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20), default="like")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)


class Report(TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_target", "target_type", "target_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    target_type: Mapped[str] = mapped_column(String(20))  # discussion | comment
    target_id: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(40))
    details: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)  # open | resolved | dismissed
    resolution_note: Mapped[str | None] = mapped_column(String(500))
    resolved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    reporter: Mapped[User | None] = relationship(foreign_keys=[reporter_id])


# ---------------------------------------------------------------------------
# Notifications, analytics, contact
# ---------------------------------------------------------------------------


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_unread", "user_id", "read_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # announcement | event | community | account | council_update
    type: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(1000), default="")
    link: Mapped[str | None] = mapped_column(String(300))
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)


class ContentViewStat(Base):
    """Aggregated daily view counts (no per-user tracking)."""

    __tablename__ = "content_view_stats"
    __table_args__ = (UniqueConstraint("content_type", "content_id", "day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    content_type: Mapped[str] = mapped_column(String(20))  # project | news | event | discussion
    content_id: Mapped[int] = mapped_column(Integer)
    day: Mapped[date] = mapped_column(Date, index=True)
    views: Mapped[int] = mapped_column(Integer, default=0)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)


# ---------------------------------------------------------------------------
# Moderation word list and the principal's profile
# ---------------------------------------------------------------------------


class BlockedTerm(TimestampMixin, Base):
    """Words/phrases filtered from community content and public profile fields.

    ``block`` rejects the post outright; ``review`` publishes it hidden and
    places it in the moderation queue."""

    __tablename__ = "blocked_terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(String(120), unique=True)
    severity: Mapped[str] = mapped_column(String(10), default="block")  # block | review
    category: Mapped[str] = mapped_column(String(30), default="insult")  # insult | profanity | hate | threat
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class PrincipalProfile(TimestampMixin, Base):
    """Single-row profile of Sen. Philip Aduda, edited by administrators.

    Factual fields should only contain verified information; timeline
    entries carry their own source."""

    __tablename__ = "principal_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Sen. Philip Aduda")
    title: Mapped[str] = mapped_column(String(200), default="")
    tagline: Mapped[str] = mapped_column(String(300), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    biography: Mapped[str] = mapped_column(Text, default="")
    photo_url: Mapped[str | None] = mapped_column(String(500))
    photo_alt: Mapped[str | None] = mapped_column(String(300))
    timeline: Mapped[list] = mapped_column(JSON, default=list)  # [{year, title, description, source}]
    gallery: Mapped[list] = mapped_column(JSON, default=list)  # [{url, alt, caption}]
    links: Mapped[list] = mapped_column(JSON, default=list)  # [{label, url}]
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
