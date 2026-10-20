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


class LayoutSql(Base):
    """The current layout of each terminal asset: a projection of the
    layout words on the bus, one row per TerminalAsset, upserted on the
    GNodeId. The payload is the word verbatim; readers decode it through
    their codec as they decode a messages row."""

    __tablename__ = "layouts"

    # The TerminalAsset GNodeId, the one link to a house.
    ta_g_node_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    terminal_asset_alias: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # The sender of the message the payload came from, as messages.from_alias
    # spells it. A row the registry wrote is not overwritten by a scada.
    from_alias: Mapped[str] = mapped_column(String, nullable=False)

    type_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # The journaled messages row the payload came from.
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)

    # The sender's clock when the layout was asserted — the do-not-regress
    # guard's per-row memory: a write with an older send time is skipped.
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
