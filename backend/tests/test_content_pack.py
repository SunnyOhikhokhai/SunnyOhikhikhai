from sqlalchemy import func, select

from app.content_pack import LEGISLATION, NEWS, PROJECTS, SOURCES, apply
from app.database import SessionLocal
from app.models import Source
from tests.conftest import Api


def _import():
    with SessionLocal() as db:
        return apply(db)


def test_import_is_idempotent_and_replaces_samples(api):
    first = _import()
    second = _import()
    assert first["projects_added"] == len(PROJECTS) and first["legislation_added"] == len(LEGISLATION)
    assert first["elections_added"] == 3 and first["news_added"] == len(NEWS) == 12
    assert first["profile_updated"] and first["retired"] > 0  # sample records and articles removed
    assert second == {k: (False if k == "profile_updated" else 0) for k in second}

    records = api.get("/api/projects", params={"page_size": 100}).json()
    assert records["meta"]["total"] == len(PROJECTS)  # no duplicates, no samples
    assert all(not r["is_demo"] and r["source_count"] >= 1 for r in records["data"])
    assert {r["verification_status"] for r in records["data"]} == {"reported"}  # never upgraded to verified

    with SessionLocal() as db:
        urls = db.scalars(select(Source.url).where(Source.url.is_not(None))).all()
        assert len(urls) == len(set(urls)) == sum(1 for s in SOURCES.values() if s["url"])
        assert db.scalar(select(func.count()).select_from(Source)) == len(SOURCES)


def test_projects_preserve_status_cost_and_source(api):
    _import()
    road = api.get("/api/projects/bwari-01-global-suite-road-sabon-gari").json()["data"]
    assert road["area_council"]["slug"] == "bwari"
    assert road["reported_length"] == "6 km" and road["reported_cost"] == "₦1.4 billion"
    assert road["sources"][0]["publisher"] == "Gazette Nigeria"
    assert "facilitated/attracted" in road["description"] and "personally funded" not in road["description"]

    ongoing = api.get("/api/projects", params={"project_status": "ongoing", "page_size": 100}).json()["data"]
    assert ongoing and all(r["status_note"] == "Reported ongoing in 2023." for r in ongoing)
    assert not api.get("/api/projects", params={"project_status": "completed"}).json()["data"]

    kuje = api.get("/api/projects", params={"area_council": "kuje", "category": "education"}).json()["data"]
    assert [r["project_status"] for r in kuje] == ["nearing_completion"]
    for council in ("amac", "bwari", "gwagwalada", "kuje", "kwali", "abaji"):
        assert api.get("/api/projects", params={"area_council": council}).json()["meta"]["total"] >= 2

    scholarship = api.get("/api/projects", params={"q": "Scholarship"}).json()["data"][0]
    assert "2018/2019 round" in scholarship["summary"]


def test_legislation_stages_are_not_collapsed(api):
    _import()
    rows = api.get("/api/legislation", params={"page_size": 50}).json()["data"]
    assert len(rows) == 13
    stages = {r["title"]: r["legislative_stage"] for r in rows}
    assert stages["FCT Area Councils Administrative & Political Structure Bill"] == "second_reading"
    assert stages["Federal Capital Territory University of Science & Technology, Abaji Bill"] == "committee_stage"
    assert stages["FCT Water Board Bill"] == "self_reported_passed"
    assert "assented" not in stages.values() and "passed_chamber" not in stages.values()
    verified = [r for r in rows if r["verification_status"] == "verified"]
    assert len(verified) == 2 and all(s["source_type"] == "national_assembly" for r in verified for s in r["sources"])
    assert all(r["sources"] for r in rows)

    health = api.get("/api/legislation", params={"category": "Health", "stage": "self_reported_passed"}).json()["data"]
    assert [r["bill_number"] for r in health] == ["SB 668"]
    assert api.get("/api/legislation", params={"year": 2017}).json()["meta"]["total"] == 1
    detail = api.get(f"/api/legislation/{rows[0]['slug']}").json()["data"]
    assert detail["sources"][0]["url"]
    found = api.get("/api/search", params={"q": "Water Board"}).json()["data"]
    assert found["legislation"][0]["title"] == "FCT Water Board Bill"


def test_elections_and_inec_2027(api):
    _import()
    rows = api.get("/api/elections").json()["data"]
    assert [r["year"] for r in rows] == [2027, 2023, 2019]
    current = rows[0]
    assert current["is_current"] and current["party"] == "APC" and current["candidate"] == "Tanimu Philip Aduda"
    assert current["verification_status"] == "verified" and current["election_date"] == "2027-01-16"
    assert any(s["source_type"] == "inec" and "2027" in s["url"] for s in current["sources"])
    assert rows[2]["votes"] == 263055 and rows[2]["votes_note"].startswith("Vote total reported")
    home = api.get("/api/home").json()["data"]
    assert home["election"]["year"] == 2027 and home["legislation_count"] == 13


def test_profile_and_news(api):
    _import()
    p = api.get("/api/profile").json()["data"]
    assert p["name"] == "Senator Philip Tanimu Aduda, CON"
    assert p["title"] == "Former FCT Senator (2011–2023)"
    assert p["tagline"] == "APC Candidate — FCT Senatorial District, 2027"
    assert p["photo_url"] is None and p["photo_source_url"] == "https://senatoraduda.com.ng/about/"
    assert p["photo_usage"] == "Primary profile portrait"
    assert p["metrics_note"] == "Self-reported figures published by Senator Aduda's official platform."
    assert [m["value"] for m in p["metrics"]] == ["140+", "160+", "1,000+", "50+"]
    quals = [f["value"] for f in p["facts"] if f["label"].startswith("Qualification")]
    assert quals == ["Higher Diploma in Public Administration", "Diploma in Social Work"]  # kept separate
    assert all(t["source"] and t["verification"] for t in p["timeline"])

    news = api.get("/api/news", params={"page_size": 50}).json()
    assert news["meta"]["total"] == 12 and all(n["verification_status"] for n in news["data"])
    month = api.get("/api/meta").json()["data"]["news_months"][0]
    assert api.get("/api/news", params={"month": month}).json()["meta"]["total"] == 12
    article = api.get(f"/api/news/{news['data'][0]['slug']}").json()["data"]
    assert article["sources"] and article["sources"][0]["url"]


def test_admin_manages_legislation_sources_and_audit(admin_api):
    _import()
    body = {
        "title": "Example FCT Bill",
        "category": "Governance",
        "year": 2026,
        "legislative_stage": "introduced",
        "verification_status": "verified",
        "sources": [],
    }
    assert admin_api.post("/api/admin/legislation", body).json()["error"]["code"] == "source_required"
    src = {"name": "National Assembly of Nigeria", "url": "https://www.nass.gov.ng/news/item/157"}
    r = admin_api.post("/api/admin/legislation", {**body, "sources": [src]})
    assert r.status_code == 201, r.text
    rec = r.json()["data"]
    assert rec["status"] == "draft" and rec["sources"][0]["source_type"] == "national_assembly"  # reused registry entry
    assert Api().get(f"/api/legislation/{rec['slug']}").status_code == 404
    admin_api.post(f"/api/admin/legislation/{rec['id']}/publish")
    assert Api().get(f"/api/legislation/{rec['slug']}").status_code == 200

    sources = admin_api.get("/api/admin/sources", params={"q": "nass.gov.ng/news/item/157"}).json()["data"]
    assert len(sources) == 1 and sources[0]["usage_count"] == 3  # bill A, an article and the new bill
    dup = admin_api.post("/api/admin/sources", {"name": "Dup", "url": "https://www.nass.gov.ng/news/item/157"})
    assert dup.status_code == 409
    assert admin_api.delete(f"/api/admin/sources/{sources[0]['id']}").status_code == 409  # in use

    elections = admin_api.get("/api/admin/elections").json()["data"]
    e = next(x for x in elections if x["year"] == 2023)
    payload = {k: e[k] for k in ("year", "title", "constituency", "candidate", "party", "outcome", "votes", "votes_note", "election_date", "summary", "verification_status", "verification_note", "is_current")}
    payload["sources"] = [{"name": s["name"], "url": s["url"], "note": s["note"]} for s in e["sources"]]
    payload["verification_note"] = "Updated note"
    assert admin_api.put(f"/api/admin/elections/{e['id']}", payload).status_code == 200

    actions = {a["action"] for a in admin_api.get("/api/admin/audit-logs", params={"page_size": 50}).json()["data"]}
    assert {"legislation.created", "legislation.published", "election.updated"} <= actions


def test_project_edit_links_registry_and_status(admin_api):
    _import()
    rec = admin_api.get("/api/admin/projects", params={"q": "Pai Road"}).json()["data"][0]
    full = admin_api.get(f"/api/admin/projects/{rec['id']}").json()["data"]
    payload = {
        "title": full["title"], "category": full["category"]["slug"], "area_council": "kwali", "location": full["location"],
        "summary": full["summary"], "description": full["description"], "verification_status": "reported",
        "project_status": "completed", "status_note": "Completion confirmed by [source].", "category_label": "Roads",
        "sources": [{"title": s["title"], "publisher": s["publisher"], "url": s["url"]} for s in full["sources"]],
        "images": [], "documents": [],
    }
    r = admin_api.put(f"/api/admin/projects/{rec['id']}", payload)
    assert r.status_code == 200, r.text
    assert r.json()["data"]["project_status"] == "completed"
    assert r.json()["data"]["sources"][0]["source_type"] == "news"  # still linked to the registry entry
