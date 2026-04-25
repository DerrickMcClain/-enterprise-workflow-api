import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func, Index, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_user", "user_id"),
        Index("ix_refresh_jti", "jti"),
        UniqueConstraint("jti", name="uq_refresh_jti"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    # rotation family: all tokens in a chain share family_id; revoke family on reuse attack
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
