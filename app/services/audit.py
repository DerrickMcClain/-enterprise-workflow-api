import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def write_audit(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    description: str | None = None,
    context: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> AuditLog:
    log = AuditLog(
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        context=context,
        request_id=request_id,
    )
    db.add(log)
    return log
