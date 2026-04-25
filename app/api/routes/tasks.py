import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, func, select, desc, asc
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.storage import save_attachment_file
from app.api.deps import get_current_user, get_membership
from app.core.permissions import can_delete_tasks
from app.models import Attachment, Comment, Project, Task, User
from app.models.enums import WorkspaceRole as WR
from app.schemas.attachment import AttachmentOut
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.task import CommentCreate, CommentOut, TaskCreate, TaskOut, TaskUpdate
from app.services.audit import write_audit
from app.services.task_rules import apply_task_status_side_effects
from app.database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_task_in_workspace(db: Session, task_id: uuid.UUID) -> Task:
    t = db.get(Task, task_id)
    if not t or t.deleted_at is not None:
        raise HTTPException(404, detail="Task not found")
    p = db.get(Project, t.project_id)
    if not p or p.deleted_at is not None:
        raise HTTPException(404, detail="Project not found")
    return t


@router.get("", response_model=PaginatedResponse[TaskOut])
def list_tasks(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    p: PaginationParams = Depends(),  # noqa: B008
    project_id: uuid.UUID = Query(...),
) -> PaginatedResponse[TaskOut]:
    proj = db.get(Project, project_id)
    if not proj or proj.deleted_at is not None:
        raise HTTPException(404, detail="Project not found")
    get_membership(db, proj.workspace_id, user.id)
    total = (
        db.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project_id, Task.deleted_at.is_(None))
        )
        or 0
    )
    col = Task.position
    if p.sort == "created_at":
        col = Task.created_at
    elif p.sort == "due_at":
        col = Task.due_at
    st = desc(col) if p.order == "desc" else asc(col)
    off = (p.page - 1) * p.page_size
    q = (
        select(Task)
        .where(Task.project_id == project_id, Task.deleted_at.is_(None))
        .order_by(st)
        .offset(off)
        .limit(p.page_size)
    )
    items = list(db.execute(q).scalars().all())
    return PaginatedResponse(
        items=[TaskOut.model_validate(x) for x in items],
        total=int(total),
        page=p.page,
        page_size=p.page_size,
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    project_id: uuid.UUID = Query(...),
) -> TaskOut:
    proj = db.get(Project, project_id)
    if not proj or proj.deleted_at is not None:
        raise HTTPException(404, detail="Project not found")
    m = get_membership(db, proj.workspace_id, user.id)
    if m.role not in (WR.MEMBER, WR.MANAGER, WR.ADMIN):
        raise HTTPException(403, detail="Cannot create task")
    if body.assignee_user_id:
        get_membership(db, proj.workspace_id, body.assignee_user_id)
    t = Task(
        project_id=project_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        due_at=body.due_at,
        created_by_user_id=user.id,
        assignee_user_id=body.assignee_user_id,
    )
    apply_task_status_side_effects(t)
    db.add(t)
    db.flush()
    write_audit(
        db,
        workspace_id=proj.workspace_id,
        actor_user_id=user.id,
        action="task.create",
        resource_type="task",
        resource_id=t.id,
    )
    db.commit()
    db.refresh(t)
    return TaskOut.model_validate(t)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TaskOut:
    t = _get_task_in_workspace(db, task_id)
    p = db.get(Project, t.project_id)
    get_membership(db, p.workspace_id, user.id)  # type: ignore[union-attr]
    return TaskOut.model_validate(t)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TaskOut:
    t = _get_task_in_workspace(db, task_id)
    p = db.get(Project, t.project_id)
    m = get_membership(db, p.workspace_id, user.id)  # type: ignore[union-attr]
    if body.assignee_user_id and body.assignee_user_id != t.assignee_user_id:
        get_membership(db, p.workspace_id, body.assignee_user_id)  # type: ignore[union-attr]
    if body.title is not None:
        t.title = body.title
    if body.description is not None:
        t.description = body.description
    if body.status is not None:
        t.status = body.status
    if body.priority is not None:
        t.priority = body.priority
    if body.due_at is not None:
        t.due_at = body.due_at
    if body.position is not None:
        t.position = body.position
    if body.assignee_user_id is not None:
        t.assignee_user_id = body.assignee_user_id
    apply_task_status_side_effects(t)
    write_audit(
        db,
        workspace_id=p.workspace_id,  # type: ignore[union-attr]
        actor_user_id=user.id,
        action="task.update",
        resource_type="task",
        resource_id=t.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return TaskOut.model_validate(t)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    t = _get_task_in_workspace(db, task_id)
    p = db.get(Project, t.project_id)
    m = get_membership(db, p.workspace_id, user.id)  # type: ignore[union-attr]
    if not can_delete_tasks(m.role):
        raise HTTPException(403, detail="Cannot delete tasks")
    t.deleted_at = datetime.now(timezone.utc)
    write_audit(
        db,
        workspace_id=p.workspace_id,  # type: ignore[union-attr]
        actor_user_id=user.id,
        action="task.soft_delete",
        resource_type="task",
        resource_id=t.id,
    )
    db.add(t)
    db.commit()
    return None


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    task_id: uuid.UUID,
    body: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> CommentOut:
    t = _get_task_in_workspace(db, task_id)
    p = db.get(Project, t.project_id)
    get_membership(db, p.workspace_id, user.id)  # type: ignore[union-attr]
    c = Comment(task_id=task_id, user_id=user.id, body=body.body)
    db.add(c)
    db.flush()
    write_audit(
        db,
        workspace_id=p.workspace_id,  # type: ignore[union-attr]
        actor_user_id=user.id,
        action="comment.create",
        resource_type="comment",
        resource_id=c.id,
    )
    db.commit()
    db.refresh(c)
    return CommentOut.model_validate(c)


@router.post(
    "/{task_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED
)
async def add_attachment(
    task_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> AttachmentOut:
    t = _get_task_in_workspace(db, task_id)
    p = db.get(Project, t.project_id)
    mship = get_membership(db, p.workspace_id, user.id)  # type: ignore[union-attr]
    if mship.role not in (WR.MEMBER, WR.MANAGER, WR.ADMIN):
        raise HTTPException(403, detail="Cannot upload")
    settings = get_settings()
    ext = Path(file.filename or "").suffix.lower()
    if ext and ext not in settings.allowed_extensions_set:
        raise HTTPException(400, detail=f"Extension {ext} not allowed")
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(400, detail="File too large")
    wid = str(p.workspace_id)  # type: ignore[union-attr]
    rel = save_attachment_file(
        data,
        workspace_id=wid,
        original_name=file.filename or "upload",
        ext=ext or "",
        content_type=file.content_type,
    )
    att = Attachment(
        task_id=task_id,
        uploaded_by_user_id=user.id,
        original_filename=file.filename or "upload",
        storage_path=rel,
        content_type=file.content_type,
        size_bytes=len(data),
    )
    db.add(att)
    db.flush()
    write_audit(
        db,
        workspace_id=p.workspace_id,  # type: ignore[union-attr]
        actor_user_id=user.id,
        action="attachment.create",
        resource_type="attachment",
        resource_id=att.id,
    )
    db.commit()
    db.refresh(att)
    return AttachmentOut.model_validate(att)
