"""Role and permission catalogue. Seeded into the roles/permissions tables."""

PERMISSIONS: dict[str, str] = {
    "records.manage": "Create, edit, publish and delete Our Record entries",
    "records.verify": "Change the verification status of records",
    "news.manage": "Create, edit and publish news",
    "events.manage": "Create, edit, cancel and archive events",
    "announcements.manage": "Create, schedule and publish announcements",
    "councils.manage": "Edit Area Council information",
    "moderation.manage": "Review reports and moderate community content",
    "members.view": "View member records (including contact details)",
    "members.suspend": "Suspend and reactivate member accounts",
    "members.export": "Export permitted member data",
    "analytics.view": "View analytics dashboards",
    "admins.manage": "Assign administrative roles",
    "audit.view": "View the audit log",
    "uploads.create": "Upload images and documents",
}

ROLES: dict[str, dict] = {
    "super_admin": {
        "name": "Super Admin",
        "description": "Full access to every part of the platform.",
        "scoped": False,
        "permissions": list(PERMISSIONS),
    },
    "content_admin": {
        "name": "Content Admin",
        "description": "Manages news, records, pages and events.",
        "scoped": False,
        "permissions": [
            "records.manage",
            "records.verify",
            "news.manage",
            "events.manage",
            "announcements.manage",
            "councils.manage",
            "analytics.view",
            "uploads.create",
        ],
    },
    "area_council_admin": {
        "name": "Area Council Admin",
        "description": "Manages approved information for one assigned Area Council.",
        "scoped": True,
        "permissions": [
            "news.manage",
            "events.manage",
            "announcements.manage",
            "councils.manage",
            "uploads.create",
        ],
    },
    "moderator": {
        "name": "Moderator",
        "description": "Manages community discussions and reports.",
        "scoped": False,
        "permissions": ["moderation.manage", "members.suspend"],
    },
    "analyst": {
        "name": "Analyst",
        "description": "Views analytics without editing content.",
        "scoped": False,
        "permissions": ["analytics.view"],
    },
}
