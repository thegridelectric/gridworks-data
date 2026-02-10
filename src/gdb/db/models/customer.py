from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from gdb.db.models._base import Base

class CustomerSql(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    primary_contact: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    secondary_contact: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
