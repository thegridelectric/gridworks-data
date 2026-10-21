from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    DateTime,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gw_data.db.models._base import Base


class HouseOperatingStatusSql(Base):
    """The current operating status of each house: a projection of the
    gw.house.operating.status words on the bus, one row per TerminalAsset,
    upserted on the GNodeId. The payload is the word verbatim; readers
    decode it through their codec as they decode a messages row."""

    __tablename__ = "house_operating_status"

    # The TerminalAsset GNodeId, the one link to a house.
    ta_g_node_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    terminal_asset_alias: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # The scada the status describes, as the word's ScadaAlias spells it.
    scada_alias: Mapped[str] = mapped_column(String, nullable=False)

    # Who produced the row: "scada" when the scada sent the word, "derived"
    # when gjk built it from the layout and latest snapshot of a house whose
    # scada does not send the word yet.
    source: Mapped[str] = mapped_column(String, nullable=False)

    type_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # The journaled messages row the payload came from; null for a derived row.
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)

    # The sender's clock when the status was produced (the word's CreatedMs):
    # the do-not-regress guard's per-row memory, so an older status never
    # overwrites a newer one.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
