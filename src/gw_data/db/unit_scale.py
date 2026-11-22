"""The `gridworks.unit_scale` rows, generated from the vendored sema snapshot.

One row per value of each unit enum the journal records as a channel's
`unit_type`: `gw1.unit` (derived channels) and `spaceheat.telemetry.name`
(measured ones). The quantity is the vocabulary's, through the enum's
published quantity projection word. The scale is read off the value's
name by the convention the `gw1.unit` enum states (a scaled unit spells
its multiplier: `X100`, `Times1000`, `TimesTen`, `Milli`, `Micro`), and
the base unit comes from the map below.

The map is hand-kept. Nothing in sema states a unit's base unit or its
scale, only its quantity; a per-unit record word stating both retires
the map and the name convention.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import NamedTuple

from sqlalchemy import Connection, text

from gw_data.sema.enums import Gw1Quantity, Gw1Unit, SpaceheatTelemetryName
from gw_data.sema.types import (
    Gw1UnitQuantityProjection,
    SpaceheatTelemetryQuantityProjection,
)

UNIT_TYPES: dict[str, tuple[type[Enum], type]] = {
    "gw1.unit": (Gw1Unit, Gw1UnitQuantityProjection),
    "spaceheat.telemetry.name": (SpaceheatTelemetryName, SpaceheatTelemetryQuantityProjection),
}

# The unit `value / scale` is in, per enum value; None where the quantity
# has no unit. Every value of both enums has an entry; the test enforces it.
BASE_UNIT: dict[Enum, str | None] = {
    Gw1Unit.Unknown: None,
    Gw1Unit.Unitless: None,
    Gw1Unit.FahrenheitX100: "F",
    Gw1Unit.FahrenheitX10: "F",
    Gw1Unit.Watts: "W",
    Gw1Unit.WattHours: "Wh",
    Gw1Unit.KilowattHoursX1000: "kWh",
    Gw1Unit.Gallons: "gal",
    Gw1Unit.GpmX100: "gpm",
    Gw1Unit.Seconds: "s",
    Gw1Unit.SecondsX10: "s",
    Gw1Unit.Milliseconds: "s",
    Gw1Unit.DollarsX1000: "USD",
    Gw1Unit.MilesPerHourX1000: "mph",
    Gw1Unit.MilesPerHourX10: "mph",
    Gw1Unit.WattsPerSquareMeter: "W/m2",
    SpaceheatTelemetryName.Unknown: None,
    SpaceheatTelemetryName.RelayState: None,
    SpaceheatTelemetryName.ThermostatState: None,
    SpaceheatTelemetryName.StorageLayer: None,
    SpaceheatTelemetryName.BinaryState: None,
    SpaceheatTelemetryName.PowerW: "W",
    SpaceheatTelemetryName.WattHours: "Wh",
    SpaceheatTelemetryName.MilliWattHours: "Wh",
    SpaceheatTelemetryName.WaterTempCTimes1000: "C",
    SpaceheatTelemetryName.AirTempCTimes1000: "C",
    SpaceheatTelemetryName.CelsiusTimes100: "C",
    SpaceheatTelemetryName.WaterTempFTimes1000: "F",
    SpaceheatTelemetryName.AirTempFTimes1000: "F",
    SpaceheatTelemetryName.GpmTimes100: "gpm",
    SpaceheatTelemetryName.GallonsTimes100: "gal",
    SpaceheatTelemetryName.VoltageRmsMilliVolts: "V",
    SpaceheatTelemetryName.VoltsTimesTen: "V",
    SpaceheatTelemetryName.VoltsTimes100: "V",
    SpaceheatTelemetryName.MicroVolts: "V",
    SpaceheatTelemetryName.CurrentRmsMicroAmps: "A",
    SpaceheatTelemetryName.HzTimes100: "Hz",
    SpaceheatTelemetryName.MicroHz: "Hz",
    SpaceheatTelemetryName.PercentKeep: "%",
}

SUFFIX_SCALE = re.compile(r"(?:X|Times)(\d+)$")
WORD_SCALE = {"TimesTen": 10, "Milli": 1000, "Micro": 1_000_000}


class UnitScaleRow(NamedTuple):
    """One `gridworks.unit_scale` row. No sema word states a unit's base
    unit and scale yet; one would retire this record."""

    unit_type: str
    unit: str
    quantity: str
    base_unit: str | None
    scale: int


def scale_of(name: str) -> int:
    """The multiplier the value's name spells; 1 where it spells none."""
    m = SUFFIX_SCALE.search(name)
    if m:
        return int(m.group(1))
    for word, scale in WORD_SCALE.items():
        if word in name:
            return scale
    return 1


def unit_scale_rows() -> list[UnitScaleRow]:
    rows: list[UnitScaleRow] = []
    for unit_type, (enum, projection) in UNIT_TYPES.items():
        for value in enum:
            if value not in BASE_UNIT:
                raise KeyError(f"{unit_type} {value.name} has no base unit in BASE_UNIT")
            quantity: Gw1Quantity = projection.project(value)
            rows.append(
                UnitScaleRow(
                    unit_type=unit_type,
                    unit=value.name,
                    quantity=quantity.name,
                    base_unit=BASE_UNIT[value],
                    scale=scale_of(value.name),
                )
            )
    return rows


def write_unit_scale(conn: Connection) -> int:
    """Replace the table's rows with the snapshot's; returns the row count."""
    rows = unit_scale_rows()
    conn.execute(text("DELETE FROM gridworks.unit_scale"))
    conn.execute(
        text(
            "INSERT INTO gridworks.unit_scale (unit_type, unit, quantity, base_unit, scale) "
            "VALUES (:unit_type, :unit, :quantity, :base_unit, :scale)"
        ),
        [r._asdict() for r in rows],
    )
    return len(rows)
