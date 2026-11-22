"""The hourly functions across a unit boundary: one house records hp-lwt,
hp-ewt and buffer-depth1 in the measured enum's old spelling for one hour
and in the next era's spelling for the two hours after, primary-flow as a
derived channel (gw1.unit GpmX100). Every hour fills from its own era's
readings: the temperatures step up at the boundary and again in the third
hour, so a reader that extends the retired row's last value past its end,
into the second hour or through the hourly aggregate's LAG and LEAD into
the third, averages the two eras and fails that hour's assertions.
The third hour also has no indoor-unit power channel, a house whose heat
pump has none, so hp_kwh_el is the outdoor unit alone.

The weather GNode's observed channels sit under its own alias: the station
reports in the first hour only, the model gridpoint in the first two, and
the house's forecast channels in all three, each in its own unit, so the
hourly oat_f and ws_mph fall back station, gridpoint, forecast, and the
source columns name the channel read; ghi_w_m2 is the gridpoint's and is
empty in the hour it is silent."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from alembic import command
from sqlalchemy import text

TA = "hw1.isone.me.versant.keene.beech.ta"
WEATHER = "hw1.isone.weather"
HOUR_A = datetime(2026, 1, 8, 22, tzinfo=timezone.utc)
HOUR_B = HOUR_A + timedelta(hours=1)
HOUR_C = HOUR_A + timedelta(hours=2)
MEASURED = "spaceheat.telemetry.name"
DERIVED = "gw1.unit"

# (alias, name, unit_type, unit, value in HOUR_A, HOUR_B, HOUR_C); None = silent that hour
CHANNELS = [
    (TA, "hp-lwt", MEASURED, "WaterTempCTimes1000", 40_000, None, None),  # 40 C
    (TA, "hp-lwt", MEASURED, "CelsiusTimes100", None, 5_000, 6_000),  # 50 C, 60 C
    (TA, "hp-ewt", MEASURED, "WaterTempCTimes1000", 30_000, None, None),  # 30 C
    (TA, "hp-ewt", MEASURED, "CelsiusTimes100", None, 3_500, 4_000),  # 35 C, 40 C
    (TA, "primary-flow", DERIVED, "GpmX100", 500, 500, 500),  # 5 gpm
    (TA, "buffer-depth1", MEASURED, "WaterTempCTimes1000", 50_000, None, None),  # 50 C = 122 F
    (TA, "buffer-depth1", DERIVED, "FahrenheitX100", None, 14_000, 15_000),  # 140 F, 150 F
    (TA, "hp-idu-pwr", MEASURED, "PowerW", 1_000, 1_000, None),
    (TA, "hp-odu-pwr", MEASURED, "PowerW", 0, 0, 2_000),
    (TA, "charge-discharge-relay3", "relay.closed.or.open", "000", 0, 0, 0),
    (TA, "forecast-oat", DERIVED, "FahrenheitX100", 3_000, 3_000, 3_000),  # 30 F
    (TA, "forecast-ws", DERIVED, "MilesPerHourX1000", 3_000, 3_000, 3_000),  # 3 mph
    (WEATHER, "kmlt-temperature", DERIVED, "FahrenheitX10", 100, None, None),  # 10 F
    (WEATHER, "kmlt-windspeed", DERIVED, "MilesPerHourX10", 10, None, None),  # 1 mph
    (WEATHER, "ommillinocket-temperature", DERIVED, "FahrenheitX10", 200, 200, None),  # 20 F
    (WEATHER, "ommillinocket-windspeed", DERIVED, "MilesPerHourX10", 20, 20, None),  # 2 mph
    (WEATHER, "ommillinocket-irradiance", DERIVED, "WattsPerSquareMeter", 400, 400, None),
]

# (oat_f, oat_source, ws_mph, ws_source, ghi_w_m2) per hour
EXPECTED_WEATHER = {
    HOUR_A: (10.0, "kmlt-temperature", 1.0, "kmlt-windspeed", 400.0),
    HOUR_B: (20.0, "ommillinocket-temperature", 2.0, "ommillinocket-windspeed", 400.0),
    HOUR_C: (30.0, "forecast-oat", 3.0, "forecast-ws", None),
}

def hp_kw(lwt_c: float, ewt_c: float) -> float:
    return 500 * 5 * (lwt_c - ewt_c) * 9 / 5 / 3410


# (hp_kwh_el, hp_kwh_th, hp_avg_lwt F, hp_avg_ewt F, buffer_depth1_start F) per hour
EXPECTED = {
    HOUR_A: (1.0, hp_kw(40, 30), 104.0, 86.0, 122.0),
    HOUR_B: (1.0, hp_kw(50, 35), 122.0, 95.0, 140.0),
    HOUR_C: (2.0, hp_kw(60, 40), 140.0, 104.0, 150.0),
}


@pytest.fixture
def two_eras(alembic_config, engine):
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    with engine.begin() as conn:
        for alias, name, unit_type, unit, a, b, c in CHANNELS:
            cid = uuid.uuid4()
            # the unique key (ta, name, deactivated_date) makes the old era's row deactivated
            deactivated = HOUR_B if b is None and c is None else HOUR_C if c is None else None
            conn.execute(
                text(
                    "INSERT INTO gridworks.reading_channels (id, name, terminal_asset_alias, display_name, unit, unit_type, channel_type, deactivated_date) "
                    "VALUES (:id, :name, :ta, :name, :unit, :unit_type, 'DataChannel', :deactivated)"
                ),
                {"id": cid, "name": name, "ta": alias, "unit": unit, "unit_type": unit_type, "deactivated": deactivated},
            )
            for hour, value in ((HOUR_A, a), (HOUR_B, b), (HOUR_C, c)):
                if value is None:
                    continue
                conn.execute(
                    text(
                        "INSERT INTO gridworks.readings (channel_id, message_id, timestamp, value) "
                        "VALUES (:cid, :mid, :ts, :value)"
                    ),
                    [
                        {"cid": cid, "mid": uuid.uuid4(), "ts": hour + timedelta(minutes=m), "value": value}
                        for m in range(0, 60, 5)
                    ],
                )
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("CALL refresh_continuous_aggregate('gridworks.readings_1hr', NULL, NULL)"))
    yield
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_both_eras_feed_the_hourly_columns(two_eras, engine):
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT time_bucket, hp_kwh_el, hp_kwh_th, hp_avg_lwt, hp_avg_ewt, buffer_depth1_start "
                "FROM gridworks.calc_hourly_data(:a, :b) ORDER BY time_bucket"
            ),
            {"a": HOUR_A, "b": HOUR_C + timedelta(hours=1)},
        ).all()
    assert [r.time_bucket for r in rows] == [HOUR_A, HOUR_B, HOUR_C]
    for r in rows:
        kwh_el, kwh_th, lwt, ewt, buffer_depth1 = EXPECTED[r.time_bucket]
        assert r.hp_kwh_el == pytest.approx(kwh_el)
        assert r.hp_kwh_th == pytest.approx(kwh_th, rel=1e-3)
        assert r.hp_avg_lwt == pytest.approx(lwt)
        assert r.hp_avg_ewt == pytest.approx(ewt)
        assert r.buffer_depth1_start == pytest.approx(buffer_depth1)


def test_weather_columns_fall_back_station_gridpoint_forecast(two_eras, engine):
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT terminal_asset_alias, time_bucket, oat_f, oat_source, ws_mph, ws_source, ghi_w_m2 "
                "FROM gridworks.calc_hourly_data(:a, :b) ORDER BY time_bucket"
            ),
            {"a": HOUR_A, "b": HOUR_C + timedelta(hours=1)},
        ).all()
    # the weather GNode is not a house: no row of its own
    assert [(r.terminal_asset_alias, r.time_bucket) for r in rows] == [(TA, HOUR_A), (TA, HOUR_B), (TA, HOUR_C)]
    for r in rows:
        oat, oat_source, ws, ws_source, ghi = EXPECTED_WEATHER[r.time_bucket]
        assert r.oat_f == pytest.approx(oat)
        assert r.oat_source == oat_source
        assert r.ws_mph == pytest.approx(ws)
        assert r.ws_source == ws_source
        assert r.ghi_w_m2 == (None if ghi is None else pytest.approx(ghi))
