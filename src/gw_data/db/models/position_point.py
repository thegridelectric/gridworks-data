from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import (
    func,
    Uuid,
    DateTime,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from gw_data.db.models._base import Base
from gw_data.sema.types import PositionPointGt

class PositionPointSql(Base):
    __tablename__ = "position_points"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    latitude_micro_deg: Mapped[int] = mapped_column()
    longitude_micro_deg: Mapped[int] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def to_gt(self) -> PositionPointGt:
        """Serialize database row → ASL GT."""
        return PositionPointGt(
            id=str(self.id),
            latitude_micro_deg=self.latitude_micro_deg,
            longitude_micro_deg=self.longitude_micro_deg,
        )

    @staticmethod
    def from_gt(gt: PositionPointGt) -> "PositionPointSql":
        """Create SQL row from ASL GT after full ASL validation."""
        return PositionPointSql(
            id=uuid.UUID(gt.id),
            latitude_micro_deg=gt.latitude_micro_deg,
            longitude_micro_deg=gt.longitude_micro_deg,
        )

