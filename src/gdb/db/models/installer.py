from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gdb.db.models._base import Base

class InstallerSql(Base):
    __tablename__ = "installers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    info: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
