import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select, desc, asc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership, load_workspace
from app.core.permissions import can_manage_projects
from app.models import Project, User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.audit import write_audit
from app.services.project_rules import validate_project_status_transition
from app.database import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectOut])
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    p: PaginationParams = Depends(),  # noqa: B008
    workspace_id: uuid.UUID = Query(...),
) -> PaginatedResponse[ProjectOut]:
    get_membership(db, workspace_id, user.id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.workspace_id == workspace_id, Project.deleted_at.is_(None))
        )
        or 0
    )
    col = Project.created_at
    if p.sort == "name":
        col = Project.name
    elif p.sort == "status":
        col = Project.status
    st = desc(col) if p.order == "desc" else asc(col)
    off = (p.page - 1) * p.page_size
    q = (
        select(Project)
        .where(
            and_(Project.workspace_id == workspace_id, Project.deleted_at.is_(None))
        )
        .order_by(st)
        .offset(off)
        .limit(p.page_size)
    )
    items = list(db.execute(q).scalars().all())
    return PaginatedResponse(
        items=[ProjectOut.model_validate(x) for x in items],
        total=int(total),
        page=p.page,
        page_size=p.page_size,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    workspace_id: uuid.UUID = Query(...),
) -> ProjectOut:
    m = get_membership(db, workspace_id, user.id)
    if not can_manage_projects(m.role):
        raise HTTPException(403, detail="Cannot create projects in this role")
    load_workspace(db, workspace_id)
    proj = Project(
        workspace_id=workspace_id,
        name=body.name,
        description=body.description,
        created_by_user_id=user.id,
    )
    db.add(proj)
    db.flush()
    write_audit(
        db,
        workspace_id=workspace_id,
        actor_user_id=user.id,
        action="project.create",
        resource_type="project",
        resource_id=proj.id,
    )
    db.commit()
    db.refresh(proj)
    return ProjectOut.model_validate(proj)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ProjectOut:
    proj = db.get(Project, project_id)
    if not proj or proj.deleted_at is not None:
        raise HTTPException(404, detail="Project not found")
    get_membership(db, proj.workspace_id, user.id)
    return ProjectOut.model_validate(proj)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ProjectOut:
    proj = db.get(Project, project_id)
    if not proj or proj.deleted_at is not None:
        raise HTTPException(404, detail="Project not found")
    m = get_membership(db, proj.workspace_id, user.id)
    if not can_manage_projects(m.role):
        raise HTTPException(403, detail="Cannot change project")
    if body.name is not None:
        proj.name = body.name
    if body.description is not None:
        proj.description = body.description
    if body.status is not None and body.status != proj.status:
        validate_project_status_transition(proj.status, body.status)
        proj.status = body.status
        proj.last_status_changed_at = datetime.now(timezone.utc)
    write_audit(
        db,
        workspace_id=proj.workspace_id,
        actor_user_id=user.id,
        action="project.update",
        resource_type="project",
        resource_id=proj.id,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectOut.model_validate(proj)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    proj = db.get(Project, project_id)
    if not proj or proj.deleted_at is not None:
        raise HTTPException(404, detail="Project not found")
    m = get_membership(db, proj.workspace_id, user.id)
    if not can_manage_projects(m.role):
        raise HTTPException(403, detail="Cannot delete project")
    proj.deleted_at = datetime.now(timezone.utc)
    write_audit(
        db,
        workspace_id=proj.workspace_id,
        actor_user_id=user.id,
        action="project.soft_delete",
        resource_type="project",
        resource_id=proj.id,
    )
    db.add(proj)
    db.commit()
    return None
