from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from gw_data.db.models._base import Base
from gw_data.db.models.data_channel import DataChannelSql

class ReadingSql(Base):
    __tablename__ = "readings"
    data_channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("data_channels.id"),
        nullable=False
    )
    data_channel: Mapped[DataChannelSql] = relationship()

    # This is not a foreign key for two reasons:
    #   1. TimescaleDB does not allow foreign keys between hypertables
    #   2. We may conceivably have readings that do not have an associated message
    #       (e.g., from a server cron job or an admin action)
    #
    # Also note that since they are both hypertables, any queries that map between readings and messages 
    # should correlate based on time to improve performance.
    message_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    value: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        # TimescaleDB automatically creates this one; we need to include it so Alembic doesn't get confused
        Index("readings_timestamp_idx", timestamp.desc()),
        UniqueConstraint("data_channel_id", "timestamp", name="readings_data_channel_id_timestamp_key")
    )

    # This table does not need a true primary key -- but SQLAlchemy requires one.
    # So we define a synthetic PK out of two columns that should always be unique. 
    __mapper_args__ = {
        "primary_key": [data_channel_id, timestamp]
    }

