import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import TaskStatus


class ProductivityReportOut(BaseModel):
    workspace_id: uuid.UUID
    as_of: date
    project_count: int
    task_total: int
    task_by_status: dict[TaskStatus, int]
    overdue_task_count: int
    done_last_7_days: int
    member_count: int


class AuditLogOut(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    description: str | None
    actor_user_id: uuid.UUID | None
    created_at: datetime
    context: dict | None

    model_config = {"from_attributes": True}
