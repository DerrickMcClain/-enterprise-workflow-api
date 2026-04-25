import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: datetime | None = None
    assignee_user_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_at: datetime | None = None
    assignee_user_id: uuid.UUID | None = None
    position: int | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    position: int
    due_at: datetime | None
    created_by_user_id: uuid.UUID | None
    assignee_user_id: uuid.UUID | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class CommentOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    user_id: uuid.UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
