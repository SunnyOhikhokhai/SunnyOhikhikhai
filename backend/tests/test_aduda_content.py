from app.aduda_content import RECORDS, apply
from app.database import SessionLocal


def test_apply_is_idempotent_and_sourced(api):
    with SessionLocal() as db:
        first = apply(db)
        second = apply(db)
    assert first["records_added"] == len(RECORDS) and first["profile_updated"]
    assert second == {"records_added": 0, "profile_updated": False}  # doesn't overwrite admin edits

    data = api.get("/api/projects", params={"page_size": 50}).json()["data"]
    real = [r for r in data if not r["is_demo"]]
    assert len(real) == len(RECORDS)
    assert all(r["source_count"] >= 1 for r in real)
    assert all(r["verification_status"] in ("pending_review", "unverified") for r in real)
    featured = api.get("/api/home").json()["data"]["featured"]
    assert featured[0]["is_demo"] is False  # real records lead the carousel

    road = api.get("/api/projects/global-suites-sabon-gari-road-bwari").json()["data"]
    assert road["area_council"]["slug"] == "bwari" and len(road["sources"]) == 4
    profile = api.get("/api/profile").json()["data"]
    assert "2011–2023" in profile["title"] and len(profile["timeline"]) >= 8
    assert all(t["source"] for t in profile["timeline"])
