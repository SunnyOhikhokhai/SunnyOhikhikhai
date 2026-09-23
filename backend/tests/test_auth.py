from tests.conftest import Api, register


def test_csrf_required_for_unsafe_requests(api):
    r = api.c.post("/api/auth/login", json={"identifier": "x@y.z", "password": "x"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "csrf_failed"


def test_full_member_flow(api):
    # Registration -> verification (email + phone) -> logout -> login -> dashboard
    r = register(api)
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["user"]["email_verified"] is False
    assert data["user"]["area_council"]["slug"] == "kuje"
    assert data["user"]["phone"] == "+2348030000000"

    bad = api.post("/api/auth/verify/confirm", {"channel": "email", "code": "000000"})
    assert bad.status_code == 400
    r = api.post("/api/auth/verify/confirm", {"channel": "email", "code": data["dev_codes"]["email"]})
    assert r.json()["data"]["user"]["email_verified"] is True
    r = api.post("/api/auth/verify/confirm", {"channel": "sms", "code": data["dev_codes"]["sms"]})
    assert r.json()["data"]["user"]["phone_verified"] is True

    assert api.post("/api/auth/logout").status_code == 200
    assert api.get("/api/auth/me").json()["data"]["user"] is None

    api.login("0803 000 0000", "StrongPass123")  # phone login, local format
    dash = api.get("/api/members/dashboard").json()["data"]
    assert dash["user"]["first_name"] == "Ada"
    assert dash["area_council"]["slug"] == "kuje"
    assert dash["upcoming_events"]
    assert dash["featured_records"]
    assert dash["unread_notifications"] >= 1


def test_consent_is_opt_in(api):
    register(api, consent_event_notifications=False)
    prefs = api.get("/api/users/me/preferences").json()["data"]
    assert prefs["email_announcements"] is False
    assert prefs["email_events"] is False
    assert prefs["sms_events"] is False


def test_passwords_are_hashed_and_validated(api):
    r = register(api, password="weakpassword")
    assert r.status_code == 422
    register(api)
    from app.database import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        u = db.query(User).filter_by(email="ada@example.com").one()
        assert u.password_hash.startswith("$argon2id$")
        assert "StrongPass123" not in u.password_hash


def test_duplicate_registration_rejected(api):
    register(api)
    assert register(Api()).status_code == 409


def test_invalid_area_council_rejected(api):
    assert register(api, council="lagos").status_code == 422


def test_login_lockout(api):
    register(api)
    api.post("/api/auth/logout")
    for _ in range(5):
        assert api.post("/api/auth/login", {"identifier": "ada@example.com", "password": "Nope12345A"}).status_code == 401
    r = api.post("/api/auth/login", {"identifier": "ada@example.com", "password": "StrongPass123"})
    assert r.status_code == 423


def test_login_rate_limited(api):
    codes = [
        api.post("/api/auth/login", {"identifier": "nobody@example.com", "password": "x"}).status_code for _ in range(12)
    ]
    assert 429 in codes


def test_otp_login_and_no_enumeration(api):
    register(api)
    api.post("/api/auth/logout")
    unknown = api.post("/api/auth/otp/request", {"identifier": "ghost@example.com", "channel": "email"})
    assert unknown.status_code == 200
    assert "login" not in unknown.json()["data"].get("dev_codes", {})
    r = api.post("/api/auth/otp/request", {"identifier": "ada@example.com", "channel": "email"})
    code = r.json()["data"]["dev_codes"]["login"]
    r = api.post("/api/auth/otp/verify", {"identifier": "ada@example.com", "channel": "email", "code": code})
    assert r.status_code == 200
    # Codes are single-use.
    r = api.post("/api/auth/otp/verify", {"identifier": "ada@example.com", "channel": "email", "code": code})
    assert r.status_code == 400


def test_password_reset_revokes_sessions(api):
    register(api)
    other = Api()
    other.login("ada@example.com", "StrongPass123")
    r = api.post("/api/auth/password/forgot", {"email": "ada@example.com"})
    code = r.json()["data"]["dev_codes"]["reset"]
    assert api.post("/api/auth/password/reset", {"email": "ada@example.com", "code": code, "password": "NewStrong456"}).status_code == 200
    assert other.get("/api/users/me").status_code == 401
    api.login("ada@example.com", "NewStrong456")


def test_bearer_token_api(api):
    register(api)
    r = api.c.post("/api/auth/token", json={"identifier": "ada@example.com", "password": "StrongPass123"})
    token = r.json()["data"]["access_token"]
    fresh = Api()
    me = fresh.c.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    # Bearer clients are exempt from CSRF (no ambient cookies).
    r = fresh.c.put("/api/users/me/preferences", json={"email_events": False}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_profile_and_account_deletion(member):
    r = member.patch("/api/users/me", {"area_council": "abaji", "display_name": "Ada O."})
    assert r.json()["data"]["area_council"]["slug"] == "abaji"
    assert member.delete("/api/users/me", {"password": "wrong"}).status_code == 400
    assert member.delete("/api/users/me", {"password": "StrongPass123"}).status_code == 200
    assert member.get("/api/users/me").status_code == 401
