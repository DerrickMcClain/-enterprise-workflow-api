import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership
from app.core.permissions import role_at_least
from app.core.redis_client import get_cache_json, set_cache
from app.database import get_db
from app.models import AuditLog, Project, Task, User, WorkspaceMember
from app.models.enums import TaskStatus, WorkspaceRole
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.report import AuditLogOut, ProductivityReportOut

router = APIRouter(tags=["reports"])


@router.get("/reports/productivity", response_model=ProductivityReportOut)
def productivity(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    workspace_id: uuid.UUID = Query(...),
) -> ProductivityReportOut:
    m = get_membership(db, workspace_id, user.id)
    if not role_at_least(m.role, WorkspaceRole.MEMBER):
        raise HTTPException(403, detail="Not allowed")
    cache_key = f"dash:prod:{workspace_id}"
    cached = get_cache_json(cache_key)
    if isinstance(cached, dict) and "workspace_id" in cached:
        return ProductivityReportOut.model_validate(cached)
    as_of = date.today()
    n_projects = int(
        db.scalar(
            select(func.count())
            .select_from(Project)
            .where(Project.workspace_id == workspace_id, Project.deleted_at.is_(None))
        )
        or 0
    )
    n_members = int(
        db.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
        )
        or 0
    )
    task_q = (
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(
            and_(
                Project.workspace_id == workspace_id,
                Task.deleted_at.is_(None),
            )
        )
    )
    tasks = list(db.execute(task_q).scalars().all())
    by_status: dict[TaskStatus, int] = {s: 0 for s in TaskStatus}
    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    overdue = sum(
        1
        for t in tasks
        if t.due_at
        and t.due_at < now
        and t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)
    )
    done_7d = sum(1 for t in tasks if t.completed_at and t.completed_at >= week_ago)
    out = ProductivityReportOut(
        workspace_id=workspace_id,
        as_of=as_of,
        project_count=n_projects,
        task_total=len(tasks),
        task_by_status=by_status,
        overdue_task_count=overdue,
        done_last_7_days=done_7d,
        member_count=n_members,
    )
    set_cache(cache_key, out.model_dump(mode="json"), 60)
    return out


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogOut])
def audit_logs(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    p: PaginationParams = Depends(),  # noqa: B008
    workspace_id: uuid.UUID = Query(...),
) -> PaginatedResponse[AuditLogOut]:
    m = get_membership(db, workspace_id, user.id)
    if not role_at_least(m.role, WorkspaceRole.MANAGER):
        raise HTTPException(403, detail="Manager or admin required to view audit logs")
    total = int(
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.workspace_id == workspace_id
            )
        )
        or 0
    )
    st = desc(AuditLog.created_at) if p.order == "desc" else asc(AuditLog.created_at)
    off = (p.page - 1) * p.page_size
    items = list(
        db.execute(
            select(AuditLog)
            .where(AuditLog.workspace_id == workspace_id)
            .order_by(st)
            .offset(off)
            .limit(p.page_size)
        )
        .scalars()
        .all()
    )
    return PaginatedResponse(
        items=[AuditLogOut.model_validate(x) for x in items],
        total=total,
        page=p.page,
        page_size=p.page_size,
    )
