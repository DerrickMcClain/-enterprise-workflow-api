import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class Notification(TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user", "user_id"),
        Index("ix_notifications_workspace", "workspace_id"),
        Index("ix_notifications_unread", "read_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column("type", String(64), default="info", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    workspace: Mapped["Workspace"] = relationship()
