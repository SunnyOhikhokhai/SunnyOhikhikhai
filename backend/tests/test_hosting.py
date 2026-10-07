import os

import httpx
import pytest

from app import config
from app.config import Settings, _platform_database_url, get_settings
from app.services import storage


def test_platform_database_url_is_converted(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_URL", "postgres://u:p@host/db?sslmode=require")
    assert _platform_database_url() == "postgresql+psycopg://u:p@host/db?sslmode=require"
    monkeypatch.setenv("DATABASE_URL", "postgresql://a:b@h/d")
    assert _platform_database_url() == "postgresql+psycopg://a:b@h/d"


def test_platform_database_url_with_custom_prefix(monkeypatch):
    for k in ("DATABASE_URL", "POSTGRES_URL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NIMPA_DB_URL_UNPOOLED", "postgresql://direct@h/d")
    monkeypatch.setenv("NIMPA_DB_URL", "postgresql://pooled@h/d")
    assert _platform_database_url() == "postgresql+psycopg://pooled@h/d"


def _vercel_settings(monkeypatch, **env):
    monkeypatch.setattr(config, "ON_VERCEL", True)
    monkeypatch.delenv("NIPAM_DATABASE_URL", raising=False)
    monkeypatch.delenv("NIPAM_UPLOAD_DIR", raising=False)
    monkeypatch.setattr(config.Settings, "model_config", {**Settings.model_config, "env_file": None})
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    try:
        return get_settings()
    finally:
        get_settings.cache_clear()


def test_vercel_defaults(monkeypatch):
    s = _vercel_settings(
        monkeypatch,
        DATABASE_URL="postgres://u:p@neon/db",
        BLOB_READ_WRITE_TOKEN="tok",
        VERCEL_PROJECT_PRODUCTION_URL="nimpa.vercel.app",
        NIPAM_SECRET_KEY="x" * 40,
        NIPAM_SEED_ADMIN_EMAIL="owner@example.org",
        NIPAM_SEED_ADMIN_PASSWORD="Str0ng!Owner-Pass",
    )
    assert s.database_url == "postgresql+psycopg://u:p@neon/db"
    assert s.storage_backend == "vercel_blob" and s.upload_dir == "/tmp/uploads"
    assert s.public_base_url == "https://nimpa.vercel.app" and s.cookie_secure is True


def test_vercel_refuses_default_secrets(monkeypatch):
    with pytest.raises(RuntimeError, match="NIPAM_SECRET_KEY"):
        _vercel_settings(monkeypatch, NIPAM_SECRET_KEY="dev-insecure-change-me")
    with pytest.raises(RuntimeError, match="NIPAM_SEED_ADMIN"):
        _vercel_settings(monkeypatch, NIPAM_SECRET_KEY="y" * 40, NIPAM_SEED_ADMIN_EMAIL="admin@nipam.local")


def test_vercel_requires_a_database(monkeypatch):
    for k in list(os.environ):
        if k.endswith("_URL"):
            monkeypatch.delenv(k)
    with pytest.raises(RuntimeError, match="No database is connected"):
        _vercel_settings(
            monkeypatch,
            NIPAM_SECRET_KEY="z" * 40,
            NIPAM_SEED_ADMIN_EMAIL="owner@example.org",
            NIPAM_SEED_ADMIN_PASSWORD="Str0ng!Owner-Pass",
        )


PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def test_vercel_blob_upload(monkeypatch):
    calls = []

    def fake_put(url, content, headers, timeout):
        calls.append((url, headers))
        return httpx.Response(200, json={"url": "https://store.public.blob.vercel-storage.com/" + url.rsplit("/", 2)[-2] + "/x.png"})

    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "tok")
    monkeypatch.setattr(get_settings(), "storage_backend", "vercel_blob")
    monkeypatch.setattr(storage.httpx, "put", fake_put)
    out = storage.store_upload(PNG, "content")
    assert out["url"].startswith("https://store.public.blob.vercel-storage.com/")
    url, headers = calls[0]
    assert url.startswith("https://blob.vercel-storage.com/content/") and url.endswith(".png")
    assert headers["authorization"] == "Bearer tok" and headers["x-content-type"] == "image/png"


def test_vercel_blob_requires_token(monkeypatch):
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)
    monkeypatch.setattr(get_settings(), "storage_backend", "vercel_blob")
    with pytest.raises(storage.ApiError) as e:
        storage.store_upload(PNG, "content")
    assert e.value.status == 503


def test_first_use_setup_is_idempotent(api):
    from app.content_pack import PROJECTS
    from app.main import ensure_setup

    ensure_setup()  # imports the content pack into the seeded test database
    ensure_setup()  # second run does nothing
    assert api.get("/api/projects", params={"page_size": 100}).json()["meta"]["total"] == len(PROJECTS)


def test_vercel_requirements_match_backend():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    def packages(path):
        return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]

    assert packages(root / "requirements.txt") == packages(root / "backend" / "requirements.txt")
