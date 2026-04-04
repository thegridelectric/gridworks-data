"""
SQLAlchemy models for the GridNodeRegistry.

Each SQL row corresponds to a serialized ASL GT snapshot.
ASL types are used for validation (via the codec) before any insert/update.
"""

from __future__ import annotations
import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    Uuid,
    Enum,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from gw_data.asl.enums import GNodeStatus
from gw_data.asl.types import ConnectivityEdgeGt
from gw_data.db.models._base import Base


class ConnectivityEdgeSql(Base):
    __tablename__ = "connectivity_edges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)

    from_g_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("g_nodes.id"), index=True
    )
    to_g_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("g_nodes.id"), index=True
    )

    status: Mapped[GNodeStatus] = mapped_column(
        Enum(GNodeStatus, name="connectivity_edge_status")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "from_g_node_id", "to_g_node_id",
            name="uq_connectivity_edges_from_to"
        ),
    )

    # -------------------
    #  ASL ↔ SQL Helpers
    # -------------------

    def to_gt(self) -> ConnectivityEdgeGt:
        return ConnectivityEdgeGt(
            id=self.id,
            from_g_node_id=self.from_g_node_id,
            to_g_node_id=self.to_g_node_id,
            from_g_node_alias=self.from_g_node_alias,
            to_g_node_alias=self.to_g_node_alias,
            status=self.status,
        )

    @staticmethod
    def from_gt(gt: ConnectivityEdgeGt) -> "ConnectivityEdgeSql":
        return ConnectivityEdgeSql(
            id=gt.id,
            from_g_node_id=gt.from_g_node_id,
            to_g_node_id=gt.to_g_node_id,
            from_g_node_alias=gt.from_g_node_alias,
            to_g_node_alias=gt.to_g_node_alias,
            status=gt.status,
        )