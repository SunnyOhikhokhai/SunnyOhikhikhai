from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import get_settings
from ..errors import ApiError
from ..models import User, VerificationCode, utcnow
from ..security import new_otp, token_digest
from .email import send_email
from .sms import send_sms

PURPOSE_TEXT = {
    "verify_email": "verify your email address",
    "verify_phone": "verify your phone number",
    "login": "log in to NIPAM",
    "reset_password": "reset your NIPAM password",
}


def issue_code(db: Session, user: User, purpose: str, channel: str) -> str:
    s = get_settings()
    if channel == "sms" and (not s.sms_enabled or not user.phone):
        raise ApiError(400, "sms_unavailable", "SMS delivery is not available for this account yet.")
    now = utcnow()
    # Invalidate older outstanding codes for the same purpose/channel.
    db.execute(
        update(VerificationCode)
        .where(
            VerificationCode.user_id == user.id,
            VerificationCode.purpose == purpose,
            VerificationCode.channel == channel,
            VerificationCode.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    code = new_otp()
    db.add(
        VerificationCode(
            user_id=user.id,
            purpose=purpose,
            channel=channel,
            code_hash=token_digest(f"{user.id}:{purpose}:{code}"),
            expires_at=now + timedelta(minutes=s.otp_ttl_minutes),
        )
    )
    db.commit()
    text = (
        f"Your NIPAM code to {PURPOSE_TEXT.get(purpose, purpose)} is {code}. "
        f"It expires in {s.otp_ttl_minutes} minutes. Never share this code with anyone."
    )
    if channel == "sms":
        send_sms(user.phone, text)
    else:
        send_email(user.email, "Your NIPAM verification code", f"Hello {user.first_name},\n\n{text}\n\n— NIPAM")
    return code


def consume_code(db: Session, user: User, purpose: str, channel: str, code: str) -> None:
    s = get_settings()
    now = utcnow()
    vc = db.scalar(
        select(VerificationCode)
        .where(
            VerificationCode.user_id == user.id,
            VerificationCode.purpose == purpose,
            VerificationCode.channel == channel,
            VerificationCode.consumed_at.is_(None),
        )
        .order_by(VerificationCode.id.desc())
    )
    invalid = ApiError(400, "invalid_code", "That code is invalid or has expired. Request a new one.")
    if not vc or vc.expires_at <= now or vc.attempts >= s.otp_max_attempts:
        raise invalid
    if vc.code_hash != token_digest(f"{user.id}:{purpose}:{code.strip()}"):
        vc.attempts += 1
        db.commit()
        raise invalid
    vc.consumed_at = now
    db.commit()
