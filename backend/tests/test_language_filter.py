import pytest

from tests.conftest import Api

POST = {"category": "general-discussion", "title": "A question for the community"}


@pytest.mark.parametrize(
    "body",
    [
        "Anyone who disagrees is an idiot and should keep quiet.",
        "You are a MUMU for saying that in this group.",
        "This is f.u.c.k.i.n.g ridiculous behaviour from people.",
        "Stop being st*pid about the whole matter please.",
        "You are an 1d10t and everybody here knows it well.",
        "Those people should go back to your village now.",
        "Iiiiidiooot, that is what you are, my friend here.",
    ],
)
def test_abusive_posts_are_blocked(member, body):
    r = member.post("/api/discussions", {**POST, "body": body})
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "abusive_language"


def test_clean_posts_and_lookalike_words_are_allowed(member):
    body = "Scunthorpe, Dumbarton and Idiotbox are just words. Our code is a good ode? No: a foolproof plan for Kuje."
    r = member.post("/api/discussions", {**POST, "body": body.replace(" ode?", " plan?")})
    assert r.status_code == 201, r.text
    assert r.json()["data"]["held_for_review"] is False


def test_borderline_language_is_held_for_review(member, admin_api):
    r = member.post("/api/discussions", {**POST, "body": "This whole proposal is nonsense in my opinion, honestly."})
    assert r.status_code == 201
    d = r.json()["data"]
    assert d["held_for_review"] is True
    assert Api().get(f"/api/discussions/{d['id']}").status_code == 404  # hidden from the public
    reports = admin_api.get("/api/admin/reports").json()["data"]
    report = next(x for x in reports if x["target_id"] == d["id"])
    assert report["reporter"] is None and "language filter" in report["details"]
    admin_api.post(f"/api/admin/reports/{report['id']}/resolve", {"action": "dismiss"})
    assert Api().get(f"/api/discussions/{d['id']}").status_code == 200  # approved


def test_comments_and_profiles_are_filtered(member):
    did = member.post("/api/discussions", {**POST, "body": "Let us share ideas for improving our area."}).json()["data"]["id"]
    r = member.post(f"/api/discussions/{did}/comments", {"body": "You are a werey"})
    assert r.json()["error"]["code"] == "abusive_language"
    r = member.patch("/api/users/me", {"display_name": "Big Idiot"})
    assert r.json()["error"]["code"] == "abusive_language"


def test_repeat_offenders_are_paused(member):
    did = member.post("/api/discussions", {**POST, "body": "Let us share ideas for improving our area."}).json()["data"]["id"]
    for _ in range(5):
        r = member.post(f"/api/discussions/{did}/comments", {"body": "You are all stupid people in this group."})
        assert r.status_code == 422
    assert "paused" in r.json()["error"]["message"]
    r = member.post(f"/api/discussions/{did}/comments", {"body": "A perfectly polite message about our community."})
    assert r.status_code == 403 and r.json()["error"]["code"] == "posting_paused"


def test_admin_manages_terms(admin_api, member):
    r = admin_api.post("/api/admin/blocked-terms", {"term": "Kpakpakpa", "severity": "block", "category": "insult"})
    assert r.status_code == 201
    tid = r.json()["data"]["id"]
    blocked = member.post("/api/discussions", {**POST, "body": "What a kpakpakpa thing to say to people here."})
    assert blocked.status_code == 422
    admin_api.delete(f"/api/admin/blocked-terms/{tid}")
    allowed = member.post("/api/discussions", {**POST, "body": "What a kpakpakpa thing to say to people here."})
    assert allowed.status_code == 201
    listing = admin_api.get("/api/admin/blocked-terms").json()
    assert listing["meta"]["blocked_last_24h"] >= 1
    assert member.get("/api/admin/blocked-terms").status_code == 403


def test_principal_profile(api, admin_api, member):
    p = api.get("/api/profile").json()["data"]
    assert p["name"] == "Sen. Philip Aduda"
    assert "[VERIFIED BIOGRAPHY TO BE ADDED]" in p["summary"]
    assert api.get("/api/home").json()["data"]["profile"]["name"] == "Sen. Philip Aduda"
    body = {
        "name": "Sen. Philip Aduda",
        "title": "Test title",
        "tagline": "Test tagline",
        "summary": "Summary",
        "biography": "## Bio",
        "timeline": [{"year": "2000", "title": "Milestone", "description": "", "source": "Official record"}],
        "gallery": [{"url": "/uploads/x.png", "alt": "Photo", "caption": ""}],
        "links": [{"label": "Facebook", "url": "https://facebook.com/example"}],
    }
    assert member.put("/api/admin/profile", body).status_code == 403
    r = admin_api.put("/api/admin/profile", body)
    assert r.status_code == 200, r.text
    p = api.get("/api/profile").json()["data"]
    assert p["tagline"] == "Test tagline" and p["timeline"][0]["source"] == "Official record"
