from fastapi import Request
from sqlalchemy.orm import Session

from ..models import AuditLog
from ..security import client_ip


def audit(
    db: Session,
    actor_id: int | None,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    request: Request | None = None,
    **meta,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_address=client_ip(request) if request else None,
            meta=meta,
        )
    )
