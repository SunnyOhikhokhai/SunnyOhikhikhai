"""Password hashing, session tokens, OTP codes, CSRF and rate limiting."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Request

from .config import get_settings
from .errors import ApiError

_hasher = PasswordHasher()  # Argon2id with library-recommended parameters

SESSION_COOKIE = "nipam_session"
CSRF_COOKIE = "nipam_csrf"
CSRF_HEADER = "x-csrf-token"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hashed)
    except InvalidHashError:
        return True


# A throwaway hash so failed lookups take as long as real verifications.
_DUMMY_HASH = _hasher.hash("nipam-timing-equaliser")


def burn_password_check(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def token_digest(token: str) -> str:
    """Keyed digest so leaked database rows cannot be replayed as tokens."""
    key = get_settings().secret_key.encode()
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()


def new_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def validate_password_strength(password: str) -> None:
    problems = []
    if len(password) < 10:
        problems.append("at least 10 characters")
    if not any(c.islower() for c in password) or not any(c.isupper() for c in password):
        problems.append("upper and lower case letters")
    if not any(c.isdigit() for c in password):
        problems.append("a number")
    if problems:
        raise ApiError(422, "weak_password", "Password must contain " + ", ".join(problems) + ".")


def client_ip(request: Request) -> str:
    # Behind a trusted reverse proxy, uvicorn --proxy-headers populates client.host.
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# CSRF (double-submit cookie). Cookie-authenticated unsafe requests must echo
# the csrf cookie in the X-CSRF-Token header. Bearer-token API clients are exempt.
# ---------------------------------------------------------------------------

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def check_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    if request.headers.get("authorization", "").lower().startswith("bearer "):
        return
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise ApiError(403, "csrf_failed", "Security token missing or invalid. Please refresh and try again.")


# ---------------------------------------------------------------------------
# Rate limiting: in-process sliding window. For multi-instance deployments,
# swap for a shared store (e.g. Redis) behind the same interface.
# ---------------------------------------------------------------------------


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def rate_limit(bucket: str, limit: int, window_seconds: int):
    def dependency(request: Request) -> None:
        if not get_settings().rate_limit_enabled:
            return
        key = f"{bucket}:{client_ip(request)}"
        if not limiter.hit(key, limit, window_seconds):
            raise ApiError(429, "rate_limited", "Too many requests. Please wait a moment and try again.")

    return dependency
