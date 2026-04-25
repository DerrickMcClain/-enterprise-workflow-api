import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Uuid, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import SoftDeleteMixin, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Comment(SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_task", "task_id"),)

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
