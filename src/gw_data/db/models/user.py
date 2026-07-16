from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    Uuid,
)
from sqlalchemy.sql import func

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from gw_data.db.models._base import Base
from gw_data.db.models.user_installation_role import UserInstallationRoleSql

class UserSql(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    installation_roles: Mapped[list[UserInstallationRoleSql]] = relationship(uselist=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, is_active={self.is_active!r})"
