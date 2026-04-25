import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import WorkspaceRole


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceMemberOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole
    invited_at: datetime
    is_pending: bool

    model_config = {"from_attributes": True}


class InviteMemberIn(BaseModel):
    email: str  # will resolve user by email
    role: WorkspaceRole = WorkspaceRole.MEMBER
