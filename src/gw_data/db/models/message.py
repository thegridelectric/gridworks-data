from __future__ import annotations
from datetime import datetime
import uuid

from sqlalchemy import (
    func,
    Uuid,
    String,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gw_data.db.models._base import Base

class MessageSql(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint(
            "from_g_node_alias",
            "message_type_name",
            "message_persisted",
            name="uq_from_type_message",
        ),
        {
            'timescaledb_hypertable': {
                'time_column_name': 'message_created',
            }
        }
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)

    # This is not a foreign key because we may receive messages from gnodes that are not yet in the database
    from_g_node_alias: Mapped[str] = mapped_column(String, nullable=False)

    message_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message_persisted: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message_type_name: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[JSONB] = mapped_column(JSONB, nullable=False)

    # def to_dict(self):
    #     d = {
    #         "MessageId": self.id,
    #         "FromAlias": self.from_g_node.alias,
    #         "MessageTypeName": self.message_type_name,
    #         "MessagePersistedMs": self.message_persisted_ms,
    #         "Payload": self.payload,
    #     }
    #     if self.message_created_ms:
    #         d["MessageCreatedMs"] = self.message_created_ms
    #     return d
