from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from gw_data.db.models._base import Base


class UnitScaleSql(Base):
    """What a reading's stored integer means, one row per value of each
    unit enum the journal records in `reading_channels.unit_type`: the
    `gw1.quantity` the unit measures, the base unit the integer is a
    multiple of, and the scale such that `value / scale` is in the base
    unit. Generated from the vendored sema snapshot by
    `gw_data.db.unit_scale`, which is the table's only writer."""

    __tablename__ = "unit_scale"

    # The enum's name, as reading_channels.unit_type spells it.
    unit_type: Mapped[str] = mapped_column(String, primary_key=True)
    # The enum value, as reading_channels.unit spells it.
    unit: Mapped[str] = mapped_column(String, primary_key=True)

    # A gw1.quantity value name, from the enum's quantity projection word.
    quantity: Mapped[str] = mapped_column(String, nullable=False)

    # The unit `value / scale` is in (C, F, gpm, W, Wh, kWh, mph, W/m2, USD, ...).
    # NULL for a quantity with no unit (Unknown, Unitless).
    base_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    scale: Mapped[int] = mapped_column(BigInteger, nullable=False)
