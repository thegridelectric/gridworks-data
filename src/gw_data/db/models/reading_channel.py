from datetime import datetime
import uuid

from sqlalchemy import (
    Index,
    Uuid,
    Boolean,
    String,
    DateTime,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gw_data.db.models._base import Base

class ReadingChannelSql(Base):
    """
    Reading Channel.

    A reading channel is a source of data for readings, with metadata common to the readings.
    """

    __tablename__ = "reading_channels"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    terminal_asset_alias: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    unit_type: Mapped[str] = mapped_column(String, nullable=False)
    channel_type: Mapped[str] = mapped_column(String, nullable=False)
    deactivated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("terminal_asset_alias", "name"),
        UniqueConstraint(
            "terminal_asset_alias",
            "name",
            "deactivated_date",
            name="unique_name_terminal_asset_deactivated_date",
            postgresql_nulls_not_distinct=True 
        )
    )

    def __repr__(self):
        active_status = f"deactivated {self.deactivated_date.isoformat()}" if self.self.deactivated_date is not None else "active"
        return (
            f"<ReadingChannelSql(name='{self.name}', "
            f"unit='{self.unit}', terminal asset={self.terminal_asset_alias.split(".")[-2]}, [{active_status}])>"
            
        )

    def __str__(self):
        active_status = f"deactivated {self.deactivated_date.isoformat()}" if self.self.deactivated_date is not None else "active"
        return (
            f"ReadingChannelSql(name:{self.name},"
            f"unit: {self.unit}, terminal asset: {self.terminal_asset_alias.split(".")[-2]}, [{active_status}])"
        )

