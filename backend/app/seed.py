"""Seed reference data (roles, Area Councils, categories) and, optionally,
clearly-labelled demonstration content.

    python -m app.seed            # reference data + super admin
    python -m app.seed --demo     # also sample content and a demo member

Demo content is flagged ``is_demo`` and shown with a "Sample" badge. It makes
no factual claims: project facts are left as placeholders to be replaced with
verified information by administrators.
"""

from __future__ import annotations

import argparse
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, SessionLocal, engine
from .models import (
    AdminUser,
    Announcement,
    AreaCouncil,
    Discussion,
    DiscussionCategory,
    Event,
    MemberAreaCouncil,
    News,
    NewsCategory,
    NotificationPreference,
    Permission,
    Profile,
    Project,
    ProjectCategory,
    Role,
    User,
    utcnow,
)
from .rbac import PERMISSIONS, ROLES
from .security import hash_password

PLACEHOLDER = "[VERIFIED PROJECT INFORMATION TO BE ADDED]"

COUNCILS = [
    (
        "amac",
        "Abuja Municipal Area Council",
        "AMAC",
        "Garki",
        "Covers the Federal Capital City and many surrounding districts and satellite communities.",
    ),
    (
        "bwari",
        "Bwari Area Council",
        "Bwari",
        "Bwari",
        "In the north of the Territory, including Bwari town and communities such as Kubwa and Dutse.",
    ),
    (
        "gwagwalada",
        "Gwagwalada Area Council",
        "Gwagwalada",
        "Gwagwalada",
        "A growing council in the centre-west of the Territory and home to the main campus of the University of Abuja.",
    ),
    (
        "kuje",
        "Kuje Area Council",
        "Kuje",
        "Kuje",
        "South of the city centre, including Kuje town and its surrounding communities.",
    ),
    (
        "kwali",
        "Kwali Area Council",
        "Kwali",
        "Kwali",
        "In the south-west of the Territory, including Kwali town and nearby rural communities.",
    ),
    (
        "abaji",
        "Abaji Area Council",
        "Abaji",
        "Abaji",
        "In the far south-west of the Territory, including Abaji town and surrounding communities.",
    ),
]

PROJECT_CATEGORIES = [
    "Infrastructure",
    "Education",
    "Healthcare",
    "Roads",
    "Community Development",
    "Youth",
    "Sports",
    "Employment/Economic Development",
    "Legislative Activity",
    "Constituency Engagement",
    "Other",
]

NEWS_CATEGORIES = [
    "NIPAM Updates",
    "Community News",
    "FCT News",
    "Events",
    "Announcements",
    "Public Information",
]

DISCUSSION_CATEGORIES = [
    ("FCT Community", "Conversations about life and community across the Territory."),
    ("Area Council", "Local conversations for each of the six Area Councils."),
    ("Development", "Infrastructure, services and development in the FCT."),
    ("Events", "Discuss upcoming and past NIPAM events."),
    ("Ideas", "Constructive suggestions for the community and the platform."),
    ("General Discussion", "Anything else, within the community guidelines."),
]


def _slug(s: str) -> str:
    from .utils import slugify

    return slugify(s)


def seed_reference(db: Session) -> None:
    perms = {}
    for code, desc in PERMISSIONS.items():
        p = db.scalar(select(Permission).where(Permission.code == code))
        if not p:
            p = Permission(code=code, description=desc)
            db.add(p)
        perms[code] = p
    db.flush()
    for code, spec in ROLES.items():
        r = db.scalar(select(Role).where(Role.code == code))
        if not r:
            r = Role(code=code)
            db.add(r)
        r.name, r.description, r.is_scoped = spec["name"], spec["description"], spec["scoped"]
        r.permissions = [perms[c] for c in spec["permissions"]]

    for i, (slug, name, short, hq, summary) in enumerate(COUNCILS):
        c = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == slug))
        if not c:
            db.add(
                AreaCouncil(
                    slug=slug,
                    name=name,
                    short_name=short,
                    headquarters=hq,
                    summary=summary,
                    description=(
                        f"{name} is one of the six Area Councils of the Federal Capital Territory. "
                        "This page brings together community updates, events, public information and "
                        "documented records relating to the council area.\n\n"
                        "Council profile information is maintained by NIPAM administrators. "
                        "Detailed council facts will be added once verified."
                    ),
                    sort_order=i,
                )
            )

    for i, name in enumerate(PROJECT_CATEGORIES):
        slug = _slug(name.replace("/", " "))
        if not db.scalar(select(ProjectCategory).where(ProjectCategory.slug == slug)):
            db.add(ProjectCategory(slug=slug, name=name, sort_order=i))
    for i, name in enumerate(NEWS_CATEGORIES):
        slug = _slug(name)
        if not db.scalar(select(NewsCategory).where(NewsCategory.slug == slug)):
            db.add(NewsCategory(slug=slug, name=name, sort_order=i))
    for i, (name, desc) in enumerate(DISCUSSION_CATEGORIES):
        slug = _slug(name)
        if not db.scalar(select(DiscussionCategory).where(DiscussionCategory.slug == slug)):
            db.add(DiscussionCategory(slug=slug, name=name, description=desc, sort_order=i))
    db.commit()


def _make_user(db: Session, email: str, password: str, name: str, council_slug: str, display: str | None = None) -> User:
    u = db.scalar(select(User).where(User.email == email))
    if u:
        return u
    council = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == council_slug))
    now = utcnow()
    u = User(email=email, full_name=name, password_hash=hash_password(password), email_verified_at=now)
    u.profile = Profile(display_name=display, consent_recorded_at=now, terms_accepted_at=now)
    u.council_link = MemberAreaCouncil(area_council_id=council.id)
    u.preferences = NotificationPreference()
    db.add(u)
    db.flush()
    return u


def seed_admin(db: Session) -> User:
    s = get_settings()
    u = _make_user(db, s.seed_admin_email, s.seed_admin_password, "NIPAM Administrator", "amac", "NIPAM Team")
    role = db.scalar(select(Role).where(Role.code == "super_admin"))
    if not db.scalar(select(AdminUser).where(AdminUser.user_id == u.id)):
        db.add(AdminUser(user_id=u.id, role_id=role.id))
    db.commit()
    return u


def seed_demo(db: Session, admin: User) -> None:
    if db.scalar(select(Project.id).where(Project.is_demo.is_(True))):
        return
    now = utcnow()
    councils = {c.slug: c for c in db.scalars(select(AreaCouncil)).all()}
    pcats = {c.slug: c for c in db.scalars(select(ProjectCategory)).all()}
    ncats = {c.slug: c for c in db.scalars(select(NewsCategory)).all()}
    dcats = {c.slug: c for c in db.scalars(select(DiscussionCategory)).all()}

    samples = [
        ("Community Health Centre Record", "healthcare", "kuje", "Kuje Area Council"),
        ("Rural Road Access Record", "roads", "abaji", "Abaji Area Council"),
        ("School Facilities Record", "education", "gwagwalada", "Gwagwalada Area Council"),
        ("Youth Skills Programme Record", "youth", "bwari", "Bwari Area Council"),
        ("Water and Sanitation Record", "infrastructure", "kwali", "Kwali Area Council"),
        ("Constituency Engagement Record", "constituency-engagement", "amac", "Abuja Municipal Area Council"),
    ]
    for i, (title, cat, council, location) in enumerate(samples):
        db.add(
            Project(
                slug=_slug(f"sample {title}"),
                title=f"[Sample] {title}",
                category_id=pcats[cat].id,
                area_council_id=councils[council].id,
                location=location,
                summary=f"Demonstration entry showing how a documented record appears. {PLACEHOLDER}",
                description=(
                    "This is **sample content** created to demonstrate the Our Record library. "
                    "It does not describe a real project and makes no claim about any achievement.\n\n"
                    f"{PLACEHOLDER}\n\n"
                    "When verified information is supplied, administrators will add the project details, "
                    "dates, photographs, supporting documents and at least one source reference."
                ),
                verification_status="unverified",
                verification_note="Sample record — awaiting verified information and sources.",
                status="published",
                is_featured=i < 5,
                is_demo=True,
                published_at=now - timedelta(days=i + 1),
                created_by_id=admin.id,
            )
        )

    news = [
        (
            "Welcome to the NIPAM community platform",
            "nipam-updates",
            None,
            "announcement",
            "NIPAM's digital home connects residents and members across the six Area Councils of the FCT.",
            "NIPAM's new platform brings members and residents together in one place.\n\n"
            "## What you can do here\n\n"
            "- **Join** and choose the Area Council you live in\n"
            "- Follow **news, announcements and events** across the FCT\n"
            "- Explore **Our Record**, a library of documented public records with sources\n"
            "- Take part in **moderated community discussions**\n\n"
            "Membership is voluntary, and you control which messages you receive from your notification settings.",
        ),
        (
            "How records are documented on Our Record",
            "public-information",
            None,
            "announcement",
            "Every entry in Our Record carries a verification status and, where available, its sources.",
            "Our Record is designed to be evidence-oriented. Each record shows:\n\n"
            "- **Verification status** — *Unverified*, *Pending review*, *Verified* or *Disputed*\n"
            "- **Source / reference** — who published the information and when\n"
            "- **Location and Area Council**\n\n"
            "A record can only be marked *Verified* when at least one source is attached. "
            "Sample entries are labelled clearly and will be replaced as verified information is supplied.",
        ),
        (
            "Area Council pages are now open",
            "announcements",
            None,
            "announcement",
            "Each of the six FCT Area Councils now has its own page for local updates, events and records.",
            "AMAC, Bwari, Gwagwalada, Kuje, Kwali and Abaji each have a dedicated page with community "
            "updates, events, public information, records and discussions.\n\n"
            "Your selected Area Council personalises your dashboard. It is self-declared and is **not** "
            "a statement of electoral eligibility or voting location.",
        ),
        (
            "Community guidelines: keeping discussions constructive",
            "nipam-updates",
            None,
            "announcement",
            "Our guidelines protect members from harassment, threats, impersonation and misinformation.",
            "The community area is moderated. Hate speech, threats, harassment, impersonation, doxxing, "
            "sharing personal information and presenting unverified claims as fact are not permitted.\n\n"
            "Use the **Report** button on any post that breaks the guidelines and a moderator will review it.",
        ),
        (
            "[Sample] Kuje community update",
            "community-news",
            "kuje",
            "update",
            "Sample Area Council update showing how local news appears on council pages.",
            "This is **sample content** for demonstration.\n\n[COMMUNITY UPDATE DETAILS TO BE ADDED]",
        ),
        (
            "[Sample] Gwagwalada public information notice",
            "public-information",
            "gwagwalada",
            "update",
            "Sample public information notice for the Gwagwalada Area Council page.",
            "This is **sample content** for demonstration.\n\n[PUBLIC INFORMATION DETAILS TO BE ADDED]",
        ),
    ]
    for i, (title, cat, council, label, excerpt, body) in enumerate(news):
        db.add(
            News(
                slug=_slug(title),
                title=title,
                excerpt=excerpt,
                body=body,
                category_id=ncats[cat].id,
                area_council_id=councils[council].id if council else None,
                content_label=label,
                author_name="NIPAM Editorial Team",
                status="published",
                is_demo=True,
                is_featured=i == 0,
                published_at=now - timedelta(days=i, hours=2),
                created_by_id=admin.id,
            )
        )

    events = [
        ("Community Town Hall", "amac", 9, True),
        ("Member Orientation Session", "bwari", 16, True),
        ("Youth Community Forum", "gwagwalada", 23, True),
        ("Area Council Listening Session", "kuje", 30, True),
        ("Community Clean-up Day", "kwali", -12, False),
        ("Residents' Information Day", "abaji", -26, False),
    ]
    for title, council, days, open_ in events:
        start = (now + timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0)
        db.add(
            Event(
                slug=_slug(f"sample {title} {council}"),
                title=f"[Sample] {title} — {councils[council].short_name}",
                summary="Sample event showing how NIPAM events are listed. Details to be confirmed.",
                description=(
                    "This is a **sample event** for demonstration. Date, venue and programme are placeholders.\n\n"
                    "[EVENT DETAILS TO BE CONFIRMED]"
                ),
                starts_at=start,
                ends_at=start + timedelta(hours=3),
                location=f"[Venue to be confirmed], {councils[council].short_name}",
                area_council_id=councils[council].id,
                organizer="NIPAM",
                registration_open=open_,
                capacity=150,
                status="published",
                is_demo=True,
                notified_at=now,
                created_by_id=admin.id,
            )
        )

    db.add(
        Announcement(
            title="Complete your profile and notification preferences",
            body="Choose which updates you receive by email, SMS or in-app from your account settings.",
            link_url="/settings",
            priority="normal",
            status="published",
            publish_at=now - timedelta(days=1),
            notified_at=now,
            is_demo=True,
            created_by_id=admin.id,
        )
    )

    db.add_all(
        [
            Discussion(
                title="Welcome — introduce yourself and your Area Council",
                body=(
                    "Welcome to the NIPAM community. Tell us which Area Council you live in and what you "
                    "hope to see on the platform. Please read the community guidelines before posting."
                ),
                category_id=dcats["fct-community"].id,
                author_id=admin.id,
                is_pinned=True,
                is_demo=True,
            ),
            Discussion(
                title="What public records would you like to see documented?",
                body=(
                    "Our Record documents public projects and activities with sources. Which kinds of records "
                    "would be most useful to you and your community? Share ideas constructively."
                ),
                category_id=dcats["ideas"].id,
                author_id=admin.id,
                is_demo=True,
            ),
        ]
    )
    db.commit()

    member = _make_user(db, "member@nipam.local", "Member!Demo2026", "Demo Member", "kuje")
    db.commit()
    print(f"Demo member: {member.email} / Member!Demo2026")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="add clearly-labelled sample content")
    parser.add_argument("--create-tables", action="store_true", help="create tables without Alembic (dev only)")
    args = parser.parse_args()
    if args.create_tables:
        Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_reference(db)
        admin = seed_admin(db)
        print(f"Super admin: {admin.email}")
        if args.demo:
            if get_settings().is_production:
                raise SystemExit("Refusing to seed demo content in production.")
            seed_demo(db, admin)
    print("Seed complete.")


if __name__ == "__main__":
    main()
