import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, JSON, ForeignKey, String, Uuid, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import SoftDeleteMixin, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Attachment(SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "attachments"
    __table_args__ = (Index("ix_attachments_task", "task_id"),)

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # optional metadata
    kind: Mapped[str] = mapped_column(String(32), default="file", nullable=False)
    # Use JSON to avoid import-time DB url check; migration uses JSONB on postgres
    extra_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="attachments")
    uploaded_by: Mapped["User | None"] = relationship("User", foreign_keys=[uploaded_by_user_id])
