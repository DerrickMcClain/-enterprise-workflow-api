import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.workspace_member import WorkspaceMember
    from app.models.refresh_token import RefreshToken


class User(SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
