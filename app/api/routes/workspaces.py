import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership, load_workspace
from app.core.permissions import role_at_least
from app.database import get_db
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import InviteMemberIn, WorkspaceCreate, WorkspaceMemberOut, WorkspaceOut
from app.services.audit import write_audit

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=List[WorkspaceOut])
def list_workspaces(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[WorkspaceOut]:
    q = (
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id, Workspace.deleted_at.is_(None))
    )
    rows = db.execute(q).scalars().all()
    return [WorkspaceOut.model_validate(w) for w in rows]


@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(
    body: WorkspaceCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceOut:
    if db.execute(select(Workspace).where(Workspace.slug == body.slug)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already taken")
    ws = Workspace(name=body.name, slug=body.slug)
    db.add(ws)
    db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=WorkspaceRole.ADMIN, is_pending=False))
    write_audit(
        db,
        workspace_id=ws.id,
        actor_user_id=user.id,
        action="workspace.create",
        resource_type="workspace",
        resource_id=ws.id,
    )
    db.commit()
    db.refresh(ws)
    return WorkspaceOut.model_validate(ws)


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(
    workspace_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceOut:
    get_membership(db, workspace_id, user.id)
    ws = load_workspace(db, workspace_id)
    return WorkspaceOut.model_validate(ws)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberOut, status_code=status.HTTP_201_CREATED)
def invite_member(
    workspace_id: uuid.UUID,
    body: InviteMemberIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceMemberOut:
    load_workspace(db, workspace_id)
    m = get_membership(db, workspace_id, user.id)
    if not role_at_least(m.role, WorkspaceRole.MANAGER):
        raise HTTPException(403, detail="Manager or admin required to invite")
    if m.role == WorkspaceRole.MANAGER and body.role == WorkspaceRole.ADMIN:
        raise HTTPException(403, detail="Managers cannot invite admins")
    target = db.execute(select(User).where(User.email == body.email.lower())).scalar_one_or_none()
    if not target:
        raise HTTPException(404, detail="User with this email is not registered")
    existing = db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == target.id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, detail="User already a member")
    new_m = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=target.id,
        role=body.role,
        is_pending=False,
    )
    db.add(new_m)
    write_audit(
        db,
        workspace_id=workspace_id,
        actor_user_id=user.id,
        action="member.invite",
        resource_type="user",
        resource_id=target.id,
        context={"role": body.role.value},
    )
    db.commit()
    db.refresh(new_m)
    return WorkspaceMemberOut.model_validate(new_m)
