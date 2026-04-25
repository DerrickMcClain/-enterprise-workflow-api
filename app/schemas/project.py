import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
