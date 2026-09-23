"""Request validation schemas. Responses are built by ``serializers`` so that
private member fields are only ever emitted deliberately."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")
URL_RE = re.compile(r"^(https?://|/)[^\s<>\"']+$")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(v: str | None) -> str | None:
    if v is None:
        return None
    return _CONTROL.sub("", v).strip()


def normalise_phone(v: str | None) -> str | None:
    if not v:
        return None
    digits = re.sub(r"[\s\-()]", "", v)
    if digits.startswith("0") and len(digits) == 11:  # Nigerian local format 080...
        digits = "+234" + digits[1:]
    if not PHONE_RE.match(digits):
        raise ValueError("Enter a valid phone number, e.g. 0803 000 0000 or +234 803 000 0000")
    return digits if digits.startswith("+") else "+" + digits


class Clean(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def _strip_controls(cls, v):
        return clean_text(v) if isinstance(v, str) else v


def _check_url(v: str | None) -> str | None:
    if v in (None, ""):
        return None
    if not URL_RE.match(v):
        raise ValueError("Must be an http(s) URL or a site-relative path")
    return v


# --- Auth ------------------------------------------------------------------


class RegisterIn(Clean):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=10, max_length=128)
    area_council: str = Field(min_length=2, max_length=40)
    ward: str | None = Field(default=None, max_length=120)
    community: str | None = Field(default=None, max_length=120)
    consent_event_notifications: bool = False
    consent_announcements: bool = False
    accept_terms: bool

    _phone = field_validator("phone")(classmethod(lambda cls, v: normalise_phone(v)))

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.lower()

    @field_validator("accept_terms")
    @classmethod
    def _must_accept(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must accept the Terms of Use and Privacy Policy")
        return v


class LoginIn(Clean):
    identifier: str = Field(min_length=3, max_length=254)  # email or phone
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False


class OtpRequestIn(Clean):
    identifier: str = Field(min_length=3, max_length=254)
    channel: Literal["email", "sms"] = "email"


class OtpLoginIn(Clean):
    identifier: str = Field(min_length=3, max_length=254)
    channel: Literal["email", "sms"] = "email"
    code: str = Field(min_length=6, max_length=6)
    remember_me: bool = False


class VerifyRequestIn(Clean):
    channel: Literal["email", "sms"]


class VerifyConfirmIn(Clean):
    channel: Literal["email", "sms"]
    code: str = Field(min_length=6, max_length=6)


class ForgotPasswordIn(Clean):
    email: EmailStr


class ResetPasswordIn(Clean):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=10, max_length=128)


class ChangePasswordIn(Clean):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class DeleteAccountIn(Clean):
    password: str = Field(min_length=1, max_length=128)


# --- Member ------------------------------------------------------------------


class ProfileUpdateIn(Clean):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    display_name: str | None = Field(default=None, max_length=80)
    bio: str | None = Field(default=None, max_length=500)
    phone: str | None = None
    area_council: str | None = Field(default=None, max_length=40)
    ward: str | None = Field(default=None, max_length=120)
    community: str | None = Field(default=None, max_length=120)

    _phone = field_validator("phone")(classmethod(lambda cls, v: normalise_phone(v)))


class PreferencesIn(Clean):
    in_app_announcements: bool | None = None
    in_app_events: bool | None = None
    in_app_community: bool | None = None
    in_app_council_updates: bool | None = None
    email_announcements: bool | None = None
    email_events: bool | None = None
    email_community: bool | None = None
    sms_announcements: bool | None = None
    sms_events: bool | None = None


# --- Community ---------------------------------------------------------------


class DiscussionIn(Clean):
    title: str = Field(min_length=8, max_length=200)
    body: str = Field(min_length=20, max_length=10000)
    category: str = Field(max_length=60)
    area_council: str | None = Field(default=None, max_length=40)


class CommentIn(Clean):
    body: str = Field(min_length=2, max_length=5000)
    parent_id: int | None = None


class ReportIn(Clean):
    target_type: Literal["discussion", "comment"]
    target_id: int
    reason: Literal[
        "hate_speech",
        "threat",
        "harassment",
        "impersonation",
        "false_claim",
        "doxxing",
        "personal_information",
        "spam",
        "other",
    ]
    details: str | None = Field(default=None, max_length=1000)


class ContactIn(Clean):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=5000)


# --- Admin: content ----------------------------------------------------------


class SourceIn(Clean):
    title: str = Field(min_length=2, max_length=300)
    publisher: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=500)
    published_on: date | None = None
    notes: str | None = Field(default=None, max_length=500)
    _url = field_validator("url")(classmethod(lambda cls, v: _check_url(v)))


class ImageIn(Clean):
    url: str = Field(max_length=500)
    alt: str = Field(default="", max_length=300)
    caption: str | None = Field(default=None, max_length=300)
    credit: str | None = Field(default=None, max_length=200)
    _url = field_validator("url")(classmethod(lambda cls, v: _check_url(v)))


class DocumentIn(Clean):
    title: str = Field(min_length=2, max_length=300)
    url: str = Field(max_length=500)
    file_type: str | None = Field(default=None, max_length=20)
    _url = field_validator("url")(classmethod(lambda cls, v: _check_url(v)))


VerificationStatus = Literal["unverified", "pending_review", "verified", "disputed"]


class ProjectIn(Clean):
    title: str = Field(min_length=4, max_length=200)
    category: str = Field(max_length=60)
    area_council: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1976, le=2100)
    record_date: date | None = None
    summary: str = Field(default="", max_length=400)
    description: str = Field(default="", max_length=20000)
    verification_status: VerificationStatus = "unverified"
    verification_note: str | None = Field(default=None, max_length=500)
    is_featured: bool = False
    is_demo: bool = False
    sources: list[SourceIn] = Field(default_factory=list, max_length=20)
    images: list[ImageIn] = Field(default_factory=list, max_length=20)
    documents: list[DocumentIn] = Field(default_factory=list, max_length=20)


ContentLabel = Literal["verified_information", "announcement", "opinion", "historical_record", "update"]


class NewsIn(Clean):
    title: str = Field(min_length=4, max_length=200)
    excerpt: str = Field(default="", max_length=400)
    body: str = Field(default="", max_length=50000)
    category: str = Field(max_length=60)
    area_council: str | None = Field(default=None, max_length=40)
    content_label: ContentLabel = "update"
    source_note: str | None = Field(default=None, max_length=400)
    image_url: str | None = Field(default=None, max_length=500)
    image_alt: str | None = Field(default=None, max_length=300)
    author_name: str = Field(default="NIPAM Editorial Team", max_length=120)
    is_featured: bool = False
    is_demo: bool = False
    _url = field_validator("image_url")(classmethod(lambda cls, v: _check_url(v)))


class EventIn(Clean):
    title: str = Field(min_length=4, max_length=200)
    summary: str = Field(default="", max_length=400)
    description: str = Field(default="", max_length=20000)
    starts_at: datetime
    ends_at: datetime | None = None
    location: str = Field(min_length=2, max_length=200)
    area_council: str | None = Field(default=None, max_length=40)
    image_url: str | None = Field(default=None, max_length=500)
    organizer: str = Field(default="NIPAM", max_length=160)
    registration_open: bool = True
    capacity: int | None = Field(default=None, ge=1, le=100000)
    is_demo: bool = False
    _url = field_validator("image_url")(classmethod(lambda cls, v: _check_url(v)))


class AnnouncementIn(Clean):
    title: str = Field(min_length=4, max_length=200)
    body: str = Field(default="", max_length=5000)
    link_url: str | None = Field(default=None, max_length=500)
    area_council: str | None = Field(default=None, max_length=40)
    priority: Literal["normal", "important"] = "normal"
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    _url = field_validator("link_url")(classmethod(lambda cls, v: _check_url(v)))


class CouncilIn(Clean):
    summary: str | None = Field(default=None, max_length=600)
    description: str | None = Field(default=None, max_length=20000)
    headquarters: str | None = Field(default=None, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)
    wards: list[str] | None = Field(default=None, max_length=100)
    _url = field_validator("image_url")(classmethod(lambda cls, v: _check_url(v)))


class StatusIn(Clean):
    status: str = Field(max_length=20)


class SuspendIn(Clean):
    reason: str = Field(min_length=3, max_length=500)


class ResolveReportIn(Clean):
    action: Literal["dismiss", "remove_content", "hide_content", "suspend_author"]
    note: str | None = Field(default=None, max_length=500)


class ModerateIn(Clean):
    status: Literal["visible", "hidden", "removed"] | None = None
    is_pinned: bool | None = None
    is_locked: bool | None = None


class AdminAssignIn(Clean):
    email: EmailStr
    role: Literal["super_admin", "content_admin", "area_council_admin", "moderator", "analyst"]
    area_council: str | None = Field(default=None, max_length=40)
