import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Uuid, Index, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from app.models.enums import WorkspaceRole
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class WorkspaceMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
        Index("ix_workspace_members_workspace", "workspace_id"),
        Index("ix_workspace_members_user", "user_id"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole, name="workspace_role", native_enum=True), nullable=False
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_pending: Mapped[bool] = mapped_column(default=False, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="workspace_memberships")
