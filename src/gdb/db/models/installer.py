from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gdb.db.models._base import Base

class InstallerSql(Base):
    __tablename__ = "installers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    info: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
