from tests.conftest import Api, register

POST = {"title": "Street lighting in our area", "body": "Let's discuss how residents can report street lighting issues.", "category": "development", "area_council": "kuje"}


def test_discussion_lifecycle(member):
    r = member.post("/api/discussions", POST)
    assert r.status_code == 201, r.text
    did = r.json()["data"]["id"]
    c = member.post(f"/api/discussions/{did}/comments", {"body": "Good idea, I agree."}).json()["data"]
    reply = member.post(f"/api/discussions/{did}/comments", {"body": "Replying here.", "parent_id": c["id"]}).json()["data"]
    assert reply["parent_id"] == c["id"]
    like = member.post(f"/api/reactions?target_type=discussion&target_id={did}").json()["data"]
    assert like == {"liked": True, "reaction_count": 1}
    d = member.get(f"/api/discussions/{did}").json()["data"]
    assert d["comment_count"] == 2 and d["liked"] is True and len(d["comments"]) == 2
    assert member.delete(f"/api/comments/{c['id']}").status_code == 200


def test_unverified_cannot_post(api):
    register(api)
    assert api.post("/api/discussions", POST).status_code == 403


def test_personal_information_and_spam_blocked(member):
    bad = {**POST, "body": "Call me on 08031234567 for more details about this."}
    assert member.post("/api/discussions", bad).json()["error"]["code"] == "personal_information"
    member.post("/api/discussions", POST)
    assert member.post("/api/discussions", POST).json()["error"]["code"] == "duplicate_post"


def test_reply_notifies_author(member):
    did = member.post("/api/discussions", POST).json()["data"]["id"]
    other = Api()
    r = register(other, email="bola@example.com", phone="08040000000")
    other.post("/api/auth/verify/confirm", {"channel": "email", "code": r.json()["data"]["dev_codes"]["email"]})
    other.post(f"/api/discussions/{did}/comments", {"body": "Thanks for starting this."})
    notes = member.get("/api/notifications").json()
    assert any(n["type"] == "community" for n in notes["data"])
    assert notes["meta"]["unread"] >= 1
    member.post("/api/notifications/read-all")
    assert member.get("/api/notifications/unread-count").json()["data"]["unread"] == 0


def test_reporting_auto_hides_after_three_reporters(member):
    did = member.post("/api/discussions", POST).json()["data"]["id"]
    for i in range(3):
        a = Api()
        r = register(a, email=f"r{i}@example.com", phone=f"0805000000{i}")
        a.post("/api/auth/verify/confirm", {"channel": "email", "code": r.json()["data"]["dev_codes"]["email"]})
        assert a.post("/api/reports", {"target_type": "discussion", "target_id": did, "reason": "spam"}).status_code == 201
    assert Api().get(f"/api/discussions/{did}").status_code == 404
