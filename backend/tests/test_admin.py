from tests.conftest import Api, register

RECORD = {
    "title": "Borehole documentation",
    "category": "infrastructure",
    "area_council": "kwali",
    "location": "Kwali",
    "summary": "Test record",
    "description": "Details",
    "verification_status": "unverified",
    "sources": [],
    "images": [],
    "documents": [],
}


def test_non_admin_forbidden(member):
    assert member.get("/api/admin/stats").status_code == 403
    assert Api().get("/api/admin/stats").status_code == 401


def test_admin_stats_and_analytics(admin_api):
    s = admin_api.get("/api/admin/stats").json()["data"]
    assert s["totals"]["members"] >= 2
    assert len(s["by_council"]) == 6
    assert len(s["registration_trend"]) == 30 and len(s["membership_growth"]) == 12
    a = admin_api.get("/api/admin/analytics").json()["data"]
    assert len(a["engagement"]) == 30


def test_record_cms_and_verification_requires_source(admin_api):
    r = admin_api.post("/api/admin/projects", RECORD)
    assert r.status_code == 201, r.text
    pid, slug = r.json()["data"]["id"], r.json()["data"]["slug"]
    assert Api().get(f"/api/projects/{slug}").status_code == 404  # drafts are private
    bad = admin_api.put(f"/api/admin/projects/{pid}", {**RECORD, "verification_status": "verified"})
    assert bad.json()["error"]["code"] == "source_required"
    good = admin_api.put(
        f"/api/admin/projects/{pid}",
        {**RECORD, "verification_status": "verified", "sources": [{"title": "Official gazette", "publisher": "FCTA", "url": "https://example.org/doc"}]},
    )
    assert good.status_code == 200
    admin_api.post(f"/api/admin/projects/{pid}/publish")
    pub = Api().get(f"/api/projects/{slug}").json()["data"]
    assert pub["verification_status"] == "verified" and pub["sources"][0]["publisher"] == "FCTA"
    admin_api.post(f"/api/admin/projects/{pid}/unpublish")
    assert Api().get(f"/api/projects/{slug}").status_code == 404
    admin_api.delete(f"/api/admin/projects/{pid}")
    assert admin_api.get(f"/api/admin/projects/{pid}").status_code == 404


def test_news_event_announcement_publish_notifies(admin_api, member):
    n = admin_api.post("/api/admin/news", {"title": "Kuje update", "excerpt": "x", "body": "Body", "category": "community-news", "area_council": "kuje"}).json()["data"]
    admin_api.post(f"/api/admin/news/{n['id']}/publish")
    e = admin_api.post(
        "/api/admin/events",
        {"title": "Town hall", "starts_at": "2099-01-01T10:00:00Z", "location": "Kuje", "area_council": "kuje"},
    ).json()["data"]
    admin_api.post(f"/api/admin/events/{e['id']}/status?status=published")
    a = admin_api.post("/api/admin/announcements", {"title": "Important notice", "body": "Hello all"}).json()["data"]
    admin_api.post(f"/api/admin/announcements/{a['id']}/publish")
    types = {x["type"] for x in member.get("/api/notifications?page_size=50").json()["data"]}
    assert {"council_update", "event", "announcement"} <= types
    # cancel notifies registrants
    member.post(f"/api/events/{e['slug']}/register")
    admin_api.post(f"/api/admin/events/{e['id']}/status?status=cancelled")
    titles = [x["title"] for x in member.get("/api/notifications").json()["data"]]
    assert any("cancelled" in t for t in titles)


def test_scheduled_announcement_dispatch(admin_api, member):
    from app.main import run_scheduled_jobs

    a = admin_api.post(
        "/api/admin/announcements", {"title": "Scheduled item", "publish_at": "2000-01-01T00:00:00Z"}
    ).json()["data"]
    admin_api.post(f"/api/admin/announcements/{a['id']}/publish")
    run_scheduled_jobs()
    assert any(x["title"] == "Scheduled item" for x in member.get("/api/notifications").json()["data"])


def test_member_management(admin_api, member):
    members = admin_api.get("/api/admin/members", params={"area_council": "kuje"}).json()
    ada = next(m for m in members["data"] if m["full_name"] == "Ada Okafor")
    assert ada["email"] == "ada@example.com"  # super admin has members.view
    admin_api.post(f"/api/admin/members/{ada['id']}/suspend", {"reason": "Test suspension"})
    assert member.get("/api/users/me").status_code == 401  # sessions revoked
    r = member.post("/api/auth/login", {"identifier": "ada@example.com", "password": "StrongPass123"})
    assert r.json()["error"]["code"] == "account_suspended"
    admin_api.post(f"/api/admin/members/{ada['id']}/reactivate")
    member.login("ada@example.com", "StrongPass123")
    csv = admin_api.get("/api/admin/members/export").text
    assert "+234" not in csv  # phone numbers never exported
    assert "ada@example.com" in csv  # opted in to event emails


def test_roles_and_scoping(admin_api, member):
    assert admin_api.post("/api/admin/admins", {"email": "ada@example.com", "role": "area_council_admin", "area_council": "kuje"}).status_code == 200
    ok = member.post("/api/admin/news", {"title": "Kuje only", "category": "community-news", "area_council": "kuje"})
    assert ok.status_code == 201
    bad = member.post("/api/admin/news", {"title": "Bwari post", "category": "community-news", "area_council": "bwari"})
    assert bad.status_code == 403
    assert member.get("/api/admin/members").status_code == 403
    assert member.get("/api/admin/projects").status_code == 403
    # analyst: read-only analytics
    admin_api.post("/api/admin/admins", {"email": "ada@example.com", "role": "analyst"})
    assert member.get("/api/admin/analytics").status_code == 200
    assert member.post("/api/admin/news", {"title": "Nope post", "category": "community-news"}).status_code == 403
    logs = admin_api.get("/api/admin/audit-logs").json()["data"]
    assert any(entry["action"] == "admin.assigned" for entry in logs)


def test_moderation(admin_api, member):
    did = member.post("/api/discussions", {"title": "A discussion to report", "body": "This body is long enough to post.", "category": "ideas"}).json()["data"]["id"]
    reporter = Api()
    r = register(reporter, email="rep@example.com", phone="08060000000")
    reporter.post("/api/auth/verify/confirm", {"channel": "email", "code": r.json()["data"]["dev_codes"]["email"]})
    reporter.post("/api/reports", {"target_type": "discussion", "target_id": did, "reason": "harassment"})
    reports = admin_api.get("/api/admin/reports").json()["data"]
    assert reports[0]["target"]["id"] == did
    admin_api.post(f"/api/admin/reports/{reports[0]['id']}/resolve", {"action": "suspend_author", "note": "Confirmed"})
    assert Api().get(f"/api/discussions/{did}").status_code == 404
    assert member.get("/api/users/me").status_code == 401


def test_upload_validation(admin_api):
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 100
    r = admin_api.c.post("/api/admin/uploads", files={"file": ("x.png", png, "image/png")}, headers=admin_api._h())
    assert r.status_code == 201 and r.json()["data"]["url"].endswith(".png")
    evil = admin_api.c.post("/api/admin/uploads", files={"file": ("x.png", b"<script>alert(1)</script>", "image/png")}, headers=admin_api._h())
    assert evil.status_code == 415
