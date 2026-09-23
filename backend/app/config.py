from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NIPAM_", extra="ignore")

    env: str = "development"  # development | test | production
    database_url: str = "sqlite:///./nipam.db"
    secret_key: str = "dev-insecure-change-me"
    frontend_origin: str = "http://localhost:5173"
    public_base_url: str = "http://localhost:5173"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Sessions
    session_ttl_hours: int = 12
    session_remember_days: int = 30
    cookie_secure: bool = False  # must be True in production (HTTPS)
    cookie_domain: str | None = None

    # OTP / verification
    otp_ttl_minutes: int = 10
    otp_max_attempts: int = 5
    # Returns OTP codes in API responses so flows can be exercised without an
    # email/SMS provider. Never enable in production.
    dev_expose_otp: bool = True

    # Login protection
    max_failed_logins: int = 5
    lockout_minutes: int = 15

    # Providers
    email_provider: str = "console"  # console | smtp
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "NIPAM <no-reply@nipam.ng>"
    sms_provider: str = "none"  # none | console | http
    sms_http_url: str = ""
    sms_http_token: str = ""
    sms_sender_id: str = "NIPAM"

    # Storage
    storage_backend: str = "local"  # local | s3
    upload_dir: str = "./uploads"
    upload_public_url: str = "/uploads"
    max_upload_mb: int = 5
    s3_bucket: str = ""
    s3_region: str = ""
    s3_endpoint_url: str = ""
    s3_public_url: str = ""

    # Rate limiting
    rate_limit_enabled: bool = True

    # Seed
    seed_admin_email: str = "admin@nipam.local"
    seed_admin_password: str = "ChangeMe!Admin2026"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def sms_enabled(self) -> bool:
        return self.sms_provider not in ("", "none")


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production:
        if s.secret_key.startswith("dev-") or len(s.secret_key) < 32:
            raise RuntimeError("NIPAM_SECRET_KEY must be set to a strong value in production")
        if s.dev_expose_otp:
            raise RuntimeError("NIPAM_DEV_EXPOSE_OTP must be false in production")
        if not s.cookie_secure:
            raise RuntimeError("NIPAM_COOKIE_SECURE must be true in production")
    return s
