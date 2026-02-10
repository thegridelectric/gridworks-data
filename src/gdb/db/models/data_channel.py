from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gdb.db.models._base import Base

class DataChannelSql(Base):
    """
    Data Channel.

    A data channel is a concept of some collection of readings that share all characteristics
    other than time.
    """

    __tablename__ = "data_channels"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)

    start_s: Mapped[Integer] = mapped_column(Integer, nullable=True)

    g_node_id: Mapped[str] = mapped_column(
        ForeignKey("g_nodes.id"),
        nullable=False
    )

    telemetry_name: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "g_node_id",
            "name",
            name="unique_name_g_node",
        ),
    )

    def to_dict(self):
        d = {
            "Id": self.id,
            "Name": self.name,
            "DisplayName": self.display_name,
            "TelemetryName": self.telemetry_name,
        }
        if self.start_s:
            d["StartS"] = self.start_s
        return d
