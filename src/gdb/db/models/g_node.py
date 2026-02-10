from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    String,
    Enum,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from gdb.asl.enums import GNodeStatus, BaseGNodeClass
from gdb.asl.types import GNodeGt

from gdb.db.models._base import Base
from gdb.db.models.position_point import PositionPointSql

class GNodeSql(Base):
    __tablename__ = "g_nodes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    alias: Mapped[str] = mapped_column(String, index=True, unique=True)
    prev_alias: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    base_class: Mapped[BaseGNodeClass] = mapped_column(
        Enum(BaseGNodeClass, name="base_g_node_class")
    )

    g_node_class: Mapped[str] = mapped_column(String)

    status: Mapped[GNodeStatus] = mapped_column(
        Enum(GNodeStatus, name="g_node_status")
    )

    position_point_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("position_points.id"), nullable=True
    )
    position_point: Mapped[Optional[PositionPointSql]] = relationship()

    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )

    # -------------------
    #  ASL ↔ SQL Helpers
    # -------------------

    def to_gt(self) -> GNodeGt:
        """Serialize SQL row → ASL GT."""
        return GNodeGt(
            g_node_id=self.id,
            alias=self.alias,
            base_class=self.base_class,
            g_node_class=self.g_node_class,
            status=self.status,
            prev_alias=self.prev_alias,
            position_point_id=self.position_point_id,
            display_name=self.display_name,
        )

    @staticmethod
    def from_gt(gt: GNodeGt) -> "GNodeSql":
        """Create SQL model from an ASL GT instance (already validated)."""
        return GNodeSql(
            id=gt.g_node_id,
            alias=gt.alias,
            prev_alias=gt.prev_alias,
            base_class=gt.base_class,
            g_node_class=gt.g_node_class,
            status=gt.status,
            position_point_id=gt.position_point_id,
            display_name=gt.display_name,
        )
