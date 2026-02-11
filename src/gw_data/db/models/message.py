from __future__ import annotations
import uuid

from sqlalchemy import (
    Uuid,
    String,
    BigInteger,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from gw_data.db.models.g_node import GNodeSql

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from gw_data.db.models._base import Base

class MessageSql(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint(
            "from_g_node_id",
            "message_type_name",
            "message_persisted_ms",
            name="uq_from_type_message",
        ),
        {
            'timescaledb_hypertable': {
                'time_column_name': 'message_created_ms',
                'chunk_time_interval': 604800000 # 1 week
            }
        }
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    from_g_node_id: Mapped[str] = mapped_column(
        ForeignKey("g_nodes.id"),
        nullable=False
    )
    from_g_node: Mapped[GNodeSql] = relationship()

    message_created_ms: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)
    message_persisted_ms: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)

    message_type_name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[JSONB] = mapped_column(JSONB, nullable=False)

    def to_dict(self):
        d = {
            "MessageId": self.id,
            "FromAlias": self.from_g_node.alias,
            "MessageTypeName": self.message_type_name,
            "MessagePersistedMs": self.message_persisted_ms,
            "Payload": self.payload,
        }
        if self.message_created_ms:
            d["MessageCreatedMs"] = self.message_created_ms
        return d
