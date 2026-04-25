import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User
    from app.models.comment import Comment
    from app.models.attachment import Attachment


class Task(SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_project", "project_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_due", "due_at"),
        Index("ix_tasks_assignee", "assignee_user_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", native_enum=True),
        default=TaskStatus.BACKLOG,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority", native_enum=True),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # completion tracking for progress reporting
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="tasks")
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assignee_user_id])
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", order_by="Comment.created_at"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
