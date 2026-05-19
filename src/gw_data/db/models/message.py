from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import (
    Uuid,
    String,
    DateTime,
    Index
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gw_data.db.models._base import Base

class MessageSql(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, primary_key=True, index=True)

    # This is not a foreign key because we may receive messages from nodes that are not yet in the database
    from_alias: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    persisted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message_type_name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        # TimescaleDB automatically creates this one; we need to include it so Alembic doesn't get confused
        Index("messages_timestamp_idx", timestamp.desc()),
        Index(
            "ix_from_type_message",
            "from_alias",
            "message_type_name",
            "persisted_at"
        ),
        {
            'timescaledb_hypertable': {
                'time_column_name': 'timestamp',
            }
        }
    )

    def test_fn(self):
        self.abc.defe = 3
