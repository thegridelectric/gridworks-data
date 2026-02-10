from __future__ import annotations


from sqlalchemy import (
    String,
    BigInteger,
    ForeignKey
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gdb.db.models._base import Base

class ReadingSql(Base):
    __tablename__ = "readings"
    __table_args__ = (
        {
            'timescaledb_hypertable': {
                'time_column_name': 'time_ms',
                'chunk_time_interval': 604800000 # 1 week
            }
        }
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    data_channel_id: Mapped[str] = mapped_column(
        ForeignKey("data_channels.id"),
        nullable=False
    )
    message_id: Mapped[str] = mapped_column(
        ForeignKey("messages.id"),
        nullable=False,
        index=True
    )
    time_ms: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    value: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
