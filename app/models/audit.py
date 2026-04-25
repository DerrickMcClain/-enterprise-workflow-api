import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text, Uuid, Index, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_workspace", "workspace_id"),
        Index("ix_audit_created", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="audit_logs")
    actor: Mapped["User | None"] = relationship("User", foreign_keys=[actor_user_id])
