import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ProjectStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.task import Task
    from app.models.user import User


class Project(SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_workspace", "workspace_id"),
        Index("ix_projects_status", "status"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=True),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # Rule: only ACTIVE -> ON_HOLD -> COMPLETED/ARCHIVED style transitions; enforced in service
    last_status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="projects")
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Task.position"
    )
