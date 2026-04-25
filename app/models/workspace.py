from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace_member import WorkspaceMember
    from app.models.project import Project
    from app.models.audit import AuditLog


class Workspace(SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_workspaces_slug"),
        Index("ix_workspaces_slug", "slug"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)

    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
