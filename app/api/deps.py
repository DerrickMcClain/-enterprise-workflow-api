import logging
import uuid
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import role_at_least
from app.core.redis_client import is_jti_blacklisted
from app.core.security import decode_token
from app.database import get_db
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole

log = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


def get_request_id(x_request_id: Annotated[Optional[str], Header()] = None) -> str:
    return x_request_id or "-"


def get_current_user_id(
    cred: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
) -> uuid.UUID:
    if not cred or not cred.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        claims = decode_token(cred.credentials)
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
    if claims.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
    jti = str(claims.get("jti", ""))
    if jti and is_jti_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    sub = str(claims.get("sub", ""))
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")
    return uuid.UUID(sub)


def get_current_user(
    db: Annotated[Session, Depends(get_db)], user_id: Annotated[uuid.UUID, Depends(get_current_user_id)]
) -> User:
    u = db.get(User, user_id)
    if not u or u.deleted_at is not None or not u.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return u


def load_workspace(
    db: Session,
    workspace_id: uuid.UUID,
) -> Workspace:
    ws = db.get(Workspace, workspace_id)
    if not ws or ws.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


def get_membership(
    db: Session,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkspaceMember:
    m = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a member of this workspace")
    return m


def assert_workspace_role(
    m: WorkspaceMember, minimum: WorkspaceRole, *, what: str = "this action"
) -> None:
    if not role_at_least(m.role, minimum):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Role too low for {what}"
        )
