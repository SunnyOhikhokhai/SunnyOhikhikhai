from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import false, or_, select, update
from sqlalchemy.orm import Session

from .. import serializers as ser
from ..config import get_settings
from ..database import get_db
from ..deps import csrf_protect, get_current_user, get_optional_user
from ..errors import ApiError
from ..models import (
    AreaCouncil,
    MemberAreaCouncil,
    NotificationPreference,
    Profile,
    User,
    UserSession,
    utcnow,
)
from ..responses import ok
from ..schemas import (
    ForgotPasswordIn,
    LoginIn,
    OtpLoginIn,
    OtpRequestIn,
    RegisterIn,
    ResetPasswordIn,
    VerifyConfirmIn,
    VerifyRequestIn,
    normalise_phone,
)
from ..security import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    burn_password_check,
    client_ip,
    hash_password,
    needs_rehash,
    new_token,
    rate_limit,
    token_digest,
    validate_password_strength,
    verify_password,
)
from ..services.audit import audit
from ..services.notify import notify_users
from ..services.otp import consume_code, issue_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _dev_codes(**codes: str | None) -> dict:
    if not get_settings().dev_expose_otp:
        return {}
    return {"dev_codes": {k: v for k, v in codes.items() if v}}


def set_csrf_cookie(response: Response, token: str | None = None) -> str:
    s = get_settings()
    token = token or new_token(24)
    response.set_cookie(
        CSRF_COOKIE, token, httponly=False, secure=s.cookie_secure, samesite="lax", domain=s.cookie_domain, path="/"
    )
    return token


def start_session(db: Session, user: User, remember: bool, request: Request, response: Response | None) -> str:
    s = get_settings()
    token = new_token()
    ttl = timedelta(days=s.session_remember_days) if remember else timedelta(hours=s.session_ttl_hours)
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=utcnow() + ttl,
            ip_address=client_ip(request),
            user_agent=(request.headers.get("user-agent") or "")[:300],
        )
    )
    user.last_login_at = utcnow()
    user.last_seen_at = utcnow()
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()
    if response is not None:
        response.set_cookie(
            SESSION_COOKIE,
            token,
            httponly=True,
            secure=s.cookie_secure,
            samesite="lax",
            domain=s.cookie_domain,
            path="/",
            max_age=int(ttl.total_seconds()) if remember else None,
        )
        set_csrf_cookie(response)  # rotate CSRF token on privilege change
    return token


def revoke_all_sessions(db: Session, user_id: int, except_id: int | None = None) -> None:
    stmt = update(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
    if except_id:
        stmt = stmt.where(UserSession.id != except_id)
    db.execute(stmt.values(revoked_at=utcnow()), execution_options={"synchronize_session": "fetch"})


def find_user(db: Session, identifier: str) -> User | None:
    ident = identifier.strip().lower()
    conds = [User.email == ident]
    try:
        phone = normalise_phone(identifier)
        if phone:
            conds.append(User.phone == phone)
    except ValueError:
        pass
    return db.scalar(select(User).where(or_(*conds), User.deleted_at.is_(None)))


def _ensure_can_login(user: User) -> None:
    if user.status != "active":
        raise ApiError(403, "account_suspended", "This account has been suspended. Contact NIPAM support for help.")


@router.get("/csrf")
def csrf(request: Request, response: Response):
    token = request.cookies.get(CSRF_COOKIE) or set_csrf_cookie(response)
    return ok({"csrf_token": token})


@router.post("/register", status_code=201, dependencies=[Depends(csrf_protect), Depends(rate_limit("register", 5, 600))])
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    validate_password_strength(body.password)
    council = db.scalar(select(AreaCouncil).where(AreaCouncil.slug == body.area_council))
    if not council:
        raise ApiError(422, "invalid_area_council", "Please choose one of the six FCT Area Councils.")
    exists = db.scalar(
        select(User.id).where(or_(User.email == body.email, User.phone == body.phone if body.phone else false()))
    )
    if exists:
        raise ApiError(409, "account_exists", "An account with this email or phone number already exists. Try logging in.")

    now = utcnow()
    user = User(email=body.email, phone=body.phone, full_name=body.full_name, password_hash=hash_password(body.password))
    user.profile = Profile(
        ward_name=body.ward or None, community=body.community or None, consent_recorded_at=now, terms_accepted_at=now
    )
    user.council_link = MemberAreaCouncil(area_council_id=council.id)
    # Only what the member explicitly opted into. Nothing unrelated is enabled.
    user.preferences = NotificationPreference(
        in_app_announcements=True,
        in_app_events=True,
        in_app_community=True,
        in_app_council_updates=True,
        email_announcements=body.consent_announcements,
        email_events=body.consent_event_notifications,
        sms_announcements=body.consent_announcements and bool(body.phone),
        sms_events=body.consent_event_notifications and bool(body.phone),
    )
    db.add(user)
    db.flush()
    audit(
        db,
        user.id,
        "member.registered",
        "user",
        user.id,
        request,
        consents={"announcements": body.consent_announcements, "events": body.consent_event_notifications},
    )
    db.commit()

    email_code = issue_code(db, user, "verify_email", "email")
    sms_code = None
    if body.phone and get_settings().sms_enabled:
        sms_code = issue_code(db, user, "verify_phone", "sms")
    start_session(db, user, False, request, response)
    notify_users(
        db,
        [user],
        "account",
        "Welcome to NIPAM",
        f"Your account has been created and linked to {council.name}. Verify your email to take part in the community.",
        "/dashboard",
    )
    return ok(
        {
            "user": ser.me(user),
            "sms_enabled": get_settings().sms_enabled,
            **_dev_codes(email=email_code, sms=sms_code),
        }
    )


@router.post("/login", dependencies=[Depends(csrf_protect), Depends(rate_limit("login", 10, 60))])
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    user = find_user(db, body.identifier)
    invalid = ApiError(401, "invalid_credentials", "The email/phone or password is incorrect.")
    if not user:
        burn_password_check(body.password)
        raise invalid
    now = utcnow()
    if user.locked_until and user.locked_until > now:
        raise ApiError(
            423, "account_locked", "Too many failed attempts. Try again later or reset your password."
        )
    if not verify_password(body.password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= s.max_failed_logins:
            user.locked_until = now + timedelta(minutes=s.lockout_minutes)
            user.failed_login_count = 0
            audit(db, user.id, "auth.locked", "user", user.id, request)
        db.commit()
        raise invalid
    _ensure_can_login(user)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    start_session(db, user, body.remember_me, request, response)
    return ok({"user": ser.me(user)})


@router.post("/token", dependencies=[Depends(rate_limit("login", 10, 60))])
def api_token(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    """Bearer token for API clients (mobile apps, integrations). No cookies."""
    user = find_user(db, body.identifier)
    if not user or not verify_password(body.password, user.password_hash):
        if not user:
            burn_password_check(body.password)
        raise ApiError(401, "invalid_credentials", "The email/phone or password is incorrect.")
    _ensure_can_login(user)
    token = start_session(db, user, body.remember_me, request, None)
    return ok({"access_token": token, "token_type": "bearer"})


@router.post("/otp/request", dependencies=[Depends(csrf_protect), Depends(rate_limit("otp", 5, 600))])
def otp_request(body: OtpRequestIn, db: Session = Depends(get_db)):
    user = find_user(db, body.identifier)
    code = None
    if user and user.status == "active":
        if body.channel == "sms" and not user.phone_verified_at:
            raise ApiError(400, "sms_unavailable", "SMS login is only available for verified phone numbers.")
        code = issue_code(db, user, "login", body.channel)
    # Same response whether or not the account exists (no enumeration).
    return ok({"sent": True, "message": "If an account exists, a login code has been sent.", **_dev_codes(login=code)})


@router.post("/otp/verify", dependencies=[Depends(csrf_protect), Depends(rate_limit("otp-verify", 10, 600))])
def otp_verify(body: OtpLoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = find_user(db, body.identifier)
    if not user:
        raise ApiError(400, "invalid_code", "That code is invalid or has expired. Request a new one.")
    consume_code(db, user, "login", body.channel, body.code)
    _ensure_can_login(user)
    if body.channel == "email" and not user.email_verified_at:
        user.email_verified_at = utcnow()  # receiving the code proves mailbox control
    start_session(db, user, body.remember_me, request, response)
    return ok({"user": ser.me(user)})


@router.post("/logout", dependencies=[Depends(csrf_protect)])
def logout(request: Request, response: Response, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    sid = getattr(request.state, "session_id", None)
    if sid:
        sess = db.get(UserSession, sid)
        if sess:
            sess.revoked_at = utcnow()
            db.commit()
    s = get_settings()
    response.delete_cookie(SESSION_COOKIE, path="/", domain=s.cookie_domain)
    set_csrf_cookie(response)
    return ok({"logged_out": True})


@router.get("/me")
def me(user: User | None = Depends(get_optional_user)):
    return ok({"user": ser.me(user) if user else None, "sms_enabled": get_settings().sms_enabled})


@router.post("/verify/request", dependencies=[Depends(csrf_protect), Depends(rate_limit("verify", 5, 600))])
def verify_request(body: VerifyRequestIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.channel == "email":
        if user.email_verified_at:
            return ok({"sent": False, "already_verified": True})
        code = issue_code(db, user, "verify_email", "email")
    else:
        if not user.phone:
            raise ApiError(400, "no_phone", "Add a phone number to your profile first.")
        if user.phone_verified_at:
            return ok({"sent": False, "already_verified": True})
        code = issue_code(db, user, "verify_phone", "sms")
    return ok({"sent": True, **_dev_codes(**{body.channel: code})})


@router.post("/verify/confirm", dependencies=[Depends(csrf_protect), Depends(rate_limit("verify-confirm", 10, 600))])
def verify_confirm(body: VerifyConfirmIn, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    purpose = "verify_email" if body.channel == "email" else "verify_phone"
    consume_code(db, user, purpose, body.channel, body.code)
    if body.channel == "email":
        user.email_verified_at = utcnow()
    else:
        user.phone_verified_at = utcnow()
    audit(db, user.id, f"member.{purpose}", "user", user.id, request)
    db.commit()
    return ok({"user": ser.me(user)})


@router.post("/password/forgot", dependencies=[Depends(csrf_protect), Depends(rate_limit("forgot", 5, 600))])
def forgot_password(body: ForgotPasswordIn, db: Session = Depends(get_db)):
    user = find_user(db, body.email)
    code = issue_code(db, user, "reset_password", "email") if user else None
    return ok({"sent": True, "message": "If an account exists, a reset code has been sent.", **_dev_codes(reset=code)})


@router.post("/password/reset", dependencies=[Depends(csrf_protect), Depends(rate_limit("reset", 10, 600))])
def reset_password(body: ResetPasswordIn, request: Request, db: Session = Depends(get_db)):
    user = find_user(db, body.email)
    if not user:
        raise ApiError(400, "invalid_code", "That code is invalid or has expired. Request a new one.")
    validate_password_strength(body.password)
    consume_code(db, user, "reset_password", "email", body.code)
    user.password_hash = hash_password(body.password)
    user.failed_login_count = 0
    user.locked_until = None
    revoke_all_sessions(db, user.id)
    audit(db, user.id, "auth.password_reset", "user", user.id, request)
    db.commit()
    notify_users(db, [user], "account", "Your password was changed", "If this wasn't you, contact NIPAM support immediately.")
    return ok({"reset": True})
