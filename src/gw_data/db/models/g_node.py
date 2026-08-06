from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    func,
    Uuid,
    String,
    Enum,
    DateTime,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gw_data.db.models._base import Base
from gw_data.sema.enums import BaseGNodeClass, GNodeStatus

class GNodeSql(Base):
    __tablename__ = "g_nodes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    alias: Mapped[str] = mapped_column(String, index=True, unique=True)
    prev_alias: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    base_class: Mapped[BaseGNodeClass] = mapped_column(
        Enum(BaseGNodeClass, name="base_g_node_class", inherit_schema=True),
        nullable=True
    )

    g_node_class: Mapped[str] = mapped_column(String)

    status: Mapped[GNodeStatus] = mapped_column(
        Enum(GNodeStatus, name="g_node_status", inherit_schema=True)
    )

    # The registry's opaque location identity, projected verbatim. gw_data
    # holds no position content — plaintext never (PII stays out of the
    # analytics database) and ciphertext deliberately not either: location
    # data lives with the registry; the audit trail in the persistent store.
    position_point_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, nullable=True
    )

    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # # -------------------
    # #  ASL ↔ SQL Helpers
    # # -------------------

    # def to_gt(self) -> GNodeGt:
    #     """Serialize SQL row → ASL GT."""
    #     return GNodeGt(
    #         g_node_id=self.id,
    #         alias=self.alias,
    #         base_class=self.base_class,
    #         g_node_class=self.g_node_class,
    #         status=self.status,
    #         prev_alias=self.prev_alias,
    #         position_point_id=self.position_point_id,
    #         display_name=self.display_name,
    #     )

    # @staticmethod
    # def from_gt(gt: GNodeGt) -> "GNodeSql":
    #     """Create SQL model from an ASL GT instance (already validated)."""
    #     return GNodeSql(
    #         id=gt.g_node_id,
    #         alias=gt.alias,
    #         prev_alias=gt.prev_alias,
    #         base_class=gt.base_class,
    #         g_node_class=gt.g_node_class,
    #         status=gt.status,
    #         position_point_id=gt.position_point_id,
    #         display_name=gt.display_name,
    #     )
