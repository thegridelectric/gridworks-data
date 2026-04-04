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
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    in_power_metering: Mapped[bool] = mapped_column(Boolean, nullable=True)
    about_node_name: Mapped[str] = mapped_column(String, nullable=False)
    captured_by_node_name: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        Index("terminal_asset_alias", "name"),
        UniqueConstraint(
            "terminal_asset_alias",
            "name",
            name="unique_name_terminal_asset",
        )
    )

    def __repr__(self):
        ta_short = self.terminal_asset_alias.split(".")[-2]
        power_metering_status = (
            "IN POWER METERING: \n" if self.in_power_metering else ""
        )
        return (
            f"{power_metering_status}"
            f"<ReadingChannelSql(name='{self.name}', "
            f"about_node_name='{self.about_node_name}', captured_by_node_name='{self.captured_by_node_name}', "
            f"unit='{self.unit}', terminal asset: {ta_short}>"
        )

    def __str__(self):
        ta_short = self.terminal_asset_alias.split(".")[-2]
        power_metering_status = (
            "IN POWER METERING: \n" if self.in_power_metering else ""
        )
        return (
            f"{power_metering_status}"
            f"ReadingChannelSql(name:{self.name},"
            f"about_node_name: {self.about_node_name}, captured_by_node_name: {self.captured_by_node_name}, "
            f"unit: {self.unit}, terminal asset: {ta_short}"
        )

