import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["NIPAM_ENV"] = "test"
os.environ["NIPAM_DATABASE_URL"] = os.environ.get("NIPAM_TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["NIPAM_UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["NIPAM_SMS_PROVIDER"] = "console"
os.environ["NIPAM_DEV_EXPOSE_OTP"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import limiter  # noqa: E402
from app.seed import seed_admin, seed_demo, seed_reference  # noqa: E402

ADMIN = ("admin@nipam.local", "ChangeMe!Admin2026")


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    limiter.reset()
    with SessionLocal() as db:
        seed_reference(db)
        admin = seed_admin(db)
        seed_demo(db, admin)
    yield


class Api:
    """TestClient wrapper that performs the CSRF handshake like the SPA does."""

    def __init__(self):
        self.c = TestClient(app)
        self.csrf = self.c.get("/api/auth/csrf").json()["data"]["csrf_token"]

    def _h(self):
        self.csrf = self.c.cookies.get("nipam_csrf") or self.csrf
        return {"X-CSRF-Token": self.csrf}

    def get(self, url, **kw):
        return self.c.get(url, **kw)

    def post(self, url, json=None, **kw):
        return self.c.post(url, json=json, headers=self._h(), **kw)

    def put(self, url, json=None, **kw):
        return self.c.put(url, json=json, headers=self._h(), **kw)

    def patch(self, url, json=None, **kw):
        return self.c.patch(url, json=json, headers=self._h(), **kw)

    def delete(self, url, json=None, **kw):
        return self.c.request("DELETE", url, json=json, headers=self._h(), **kw)

    def login(self, email, password):
        r = self.post("/api/auth/login", {"identifier": email, "password": password})
        assert r.status_code == 200, r.text
        return r


@pytest.fixture
def api():
    return Api()


@pytest.fixture
def admin_api():
    a = Api()
    a.login(*ADMIN)
    return a


def register(api: Api, email="ada@example.com", phone="08030000000", council="kuje", **extra):
    payload = {
        "full_name": "Ada Okafor",
        "email": email,
        "phone": phone,
        "password": "StrongPass123",
        "area_council": council,
        "ward": "",
        "community": "",
        "consent_event_notifications": True,
        "consent_announcements": False,
        "accept_terms": True,
        **extra,
    }
    return api.post("/api/auth/register", payload)


@pytest.fixture
def member(api):
    r = register(api)
    assert r.status_code == 201, r.text
    code = r.json()["data"]["dev_codes"]["email"]
    assert api.post("/api/auth/verify/confirm", {"channel": "email", "code": code}).status_code == 200
    return api
