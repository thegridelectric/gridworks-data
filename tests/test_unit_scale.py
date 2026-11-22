"""The unit_scale rows: every value of both unit enums resolves to a row
whose quantity is the projection word's and whose scale is the one the
name spells; the migration fills the table with them; and every
(unit_type, unit) the journal's reading_channels record today in either
enum finds its row."""

import pytest
from sqlalchemy import text

from gw_data.db.unit_scale import UnitScaleRow, scale_of, unit_scale_rows
from gw_data.sema.enums import Gw1Unit, SpaceheatTelemetryName

# Distinct (unit_type, unit) pairs of reading_channels in the two unit
# enums, journaldb 2026-11-16.
JOURNAL_PAIRS = [
    ("gw1.unit", u)
    for u in (
        "DollarsX1000", "FahrenheitX10", "FahrenheitX100", "GpmX100", "KilowattHoursX1000",
        "MilesPerHourX10", "MilesPerHourX1000", "Unitless", "Unknown", "WattHours", "Watts",
        "WattsPerSquareMeter",
    )
] + [
    ("spaceheat.telemetry.name", u)
    for u in (
        "AirTempCTimes1000", "AirTempFTimes1000", "BinaryState", "CelsiusTimes100", "GpmTimes100",
        "MicroHz", "MicroVolts", "PowerW", "RelayState", "ThermostatState", "Unknown",
        "VoltsTimes100", "VoltsTimesTen", "WaterTempCTimes1000", "WattHours",
    )
]


def test_every_enum_value_has_a_row():
    rows = {(r.unit_type, r.unit): r for r in unit_scale_rows()}
    assert {u.name for u in Gw1Unit} == {r.unit for r in rows.values() if r.unit_type == "gw1.unit"}
    assert {u.name for u in SpaceheatTelemetryName} == {
        r.unit for r in rows.values() if r.unit_type == "spaceheat.telemetry.name"
    }
    assert len(rows) == len(Gw1Unit) + len(SpaceheatTelemetryName)


@pytest.mark.parametrize(
    "row",
    [
        UnitScaleRow("gw1.unit", "GpmX100", "FlowRate", "gpm", 100),
        UnitScaleRow("spaceheat.telemetry.name", "GpmTimes100", "FlowRate", "gpm", 100),
        UnitScaleRow("spaceheat.telemetry.name", "WaterTempCTimes1000", "Temperature", "C", 1000),
        UnitScaleRow("spaceheat.telemetry.name", "CelsiusTimes100", "Temperature", "C", 100),
        UnitScaleRow("gw1.unit", "FahrenheitX100", "Temperature", "F", 100),
        UnitScaleRow("gw1.unit", "KilowattHoursX1000", "Energy", "kWh", 1000),
        UnitScaleRow("spaceheat.telemetry.name", "WattHours", "Energy", "Wh", 1),
        UnitScaleRow("spaceheat.telemetry.name", "MicroVolts", "Voltage", "V", 1_000_000),
        UnitScaleRow("spaceheat.telemetry.name", "VoltsTimesTen", "Voltage", "V", 10),
        UnitScaleRow("gw1.unit", "Milliseconds", "Time", "s", 1000),
        UnitScaleRow("gw1.unit", "MilesPerHourX10", "WindSpeed", "mph", 10),
        UnitScaleRow("gw1.unit", "WattsPerSquareMeter", "Irradiance", "W/m2", 1),
        UnitScaleRow("spaceheat.telemetry.name", "RelayState", "Unitless", None, 1),
    ],
)
def test_known_rows(row):
    assert row in unit_scale_rows()


def test_scale_of_names():
    assert scale_of("PowerW") == 1
    assert scale_of("CurrentRmsMicroAmps") == 1_000_000
    assert scale_of("VoltageRmsMilliVolts") == 1000


def test_journal_pairs_resolve():
    rows = {(r.unit_type, r.unit) for r in unit_scale_rows()}
    assert set(JOURNAL_PAIRS) <= rows


@pytest.fixture
def at_head(alembic_config):
    from alembic import command

    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_migration_fills_the_table(at_head, engine):
    with engine.connect() as conn:
        got = {
            (r.unit_type, r.unit): (r.quantity, r.base_unit, r.scale)
            for r in conn.execute(text("SELECT * FROM gridworks.unit_scale"))
        }
    want = {(r.unit_type, r.unit): (r.quantity, r.base_unit, r.scale) for r in unit_scale_rows()}
    assert got == want
