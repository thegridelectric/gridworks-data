from __future__ import annotations
import uuid

from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gw_data.db.models._base import Base

class InstallerSql(Base):
    __tablename__ = "installers"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    info: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
