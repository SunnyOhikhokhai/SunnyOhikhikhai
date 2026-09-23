from tests.conftest import Api, register


def test_home_and_councils(api):
    d = api.get("/api/home").json()["data"]
    assert [c["slug"] for c in d["councils"]] == ["amac", "bwari", "gwagwalada", "kuje", "kwali", "abaji"]
    assert d["featured"] and all(p["is_demo"] for p in d["featured"])
    kuje = api.get("/api/area-councils/kuje").json()["data"]
    assert kuje["council"]["name"] == "Kuje Area Council"
    assert kuje["records"] and kuje["events"] and kuje["updates"]
    assert api.get("/api/area-councils/lagos").status_code == 404


def test_records_filters_and_detail(api):
    r = api.get("/api/projects", params={"area_council": "kuje"}).json()
    assert r["meta"]["total"] == 1
    assert api.get("/api/projects", params={"category": "roads"}).json()["meta"]["total"] == 1
    assert api.get("/api/projects", params={"q": "water"}).json()["meta"]["total"] == 1
    slug = r["data"][0]["slug"]
    d = api.get(f"/api/projects/{slug}").json()["data"]
    assert d["verification_status"] == "unverified"
    assert "[VERIFIED PROJECT INFORMATION TO BE ADDED]" in d["description"]
    assert "related" in d


def test_news_and_events(api):
    news = api.get("/api/news").json()
    assert news["meta"]["total"] >= 6
    slug = news["data"][0]["slug"]
    assert api.get(f"/api/news/{slug}").json()["data"]["body"]
    up = api.get("/api/events", params={"when": "upcoming"}).json()["data"]
    past = api.get("/api/events", params={"when": "past"}).json()["data"]
    assert len(up) == 4 and len(past) == 2


def test_event_registration_requires_verified_member(api):
    slug = api.get("/api/events").json()["data"][0]["slug"]
    assert api.post(f"/api/events/{slug}/register").status_code == 401
    register(api)  # logged in but unverified
    r = api.post(f"/api/events/{slug}/register")
    assert r.status_code == 403 and r.json()["error"]["code"] == "verification_required"


def test_event_registration(member):
    slug = member.get("/api/events").json()["data"][0]["slug"]
    assert member.post(f"/api/events/{slug}/register").json()["data"]["registered"]
    ev = member.get(f"/api/events/{slug}").json()["data"]
    assert ev["is_registered"] and ev["registered_count"] == 1
    assert len(member.get("/api/members/events").json()["data"]) == 1
    member.delete(f"/api/events/{slug}/register")
    assert member.get(f"/api/events/{slug}").json()["data"]["is_registered"] is False


def test_search(api):
    r = api.get("/api/search", params={"q": "kuje"}).json()
    assert r["data"]["councils"][0]["slug"] == "kuje"
    assert r["meta"]["total"] > 1
    assert api.get("/api/search", params={"q": "zzzzzz"}).json()["meta"]["total"] == 0


def test_public_apis_never_expose_contact_details(member):
    member.post("/api/discussions", {"title": "Hello from Kuje residents", "body": "A constructive post about community life in Kuje.", "category": "general-discussion"})
    anon = Api()
    for url in ["/api/home", "/api/discussions", "/api/area-councils/kuje", "/api/search?q=hello"]:
        text = anon.get(url).text
        assert "ada@example.com" not in text and "+2348030000000" not in text


def test_sitemap(api):
    r = api.get("/sitemap.xml")
    assert r.status_code == 200 and "/area-councils/kuje" in r.text
