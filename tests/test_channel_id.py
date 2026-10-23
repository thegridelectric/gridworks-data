"""The channel_id migration on a reading_channels table shaped like
journaldb before it: mapped rows take their layout Id, pseudo rows stay
NULL, and a data row the map does not cover fails the upgrade."""

import csv
import uuid

import pytest
from alembic import command
from sqlalchemy import text

BEFORE = "d4a7c9e1b2f3"
TA = "hw1.isone.me.versant.keene.oak.ta"
LAYOUT_ID = uuid.uuid4()
OLD_NAME_ROW = uuid.uuid4()  # a pre-cutover uuid4 row for vdc-relay1
NEW_NAME_ROW = uuid.uuid4()  # the uuid5 row the rename vdc-relay got
PSEUDO_ROW = uuid.uuid4()
UNCOVERED_ROW = uuid.uuid4()


def insert_row(conn, row_id, name, channel_type) -> None:
    conn.execute(
        text(
            "INSERT INTO gridworks.reading_channels (id, name, terminal_asset_alias, display_name, unit, unit_type, channel_type) "
            "VALUES (:id, :name, :ta, :name, 'RelayState', 'spaceheat.telemetry.name', :ct)"
        ),
        {"id": row_id, "name": name, "ta": TA, "ct": channel_type},
    )


def write_map(path, rows) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "channel_id"])
        w.writerows(rows)


@pytest.fixture
def before_state(alembic_config, engine, tmp_path, monkeypatch):
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, BEFORE)
    with engine.connect() as conn:
        insert_row(conn, OLD_NAME_ROW, "vdc-relay1", "data.channel.gt")
        insert_row(conn, NEW_NAME_ROW, "vdc-relay", "data.channel.gt")
        insert_row(conn, PSEUDO_ROW, "vdc-relay-state", "gjk.pseudo")
        conn.commit()
    csv_path = tmp_path / "map.csv"
    monkeypatch.setenv("GW_DATA_CHANNEL_ID_CSV", str(csv_path))
    yield csv_path
    # leave the chain at head on an empty database for the tests that follow
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_rename_rows_share_the_layout_id(before_state, alembic_config, engine):
    write_map(before_state, [(OLD_NAME_ROW, LAYOUT_ID), (NEW_NAME_ROW, LAYOUT_ID), (PSEUDO_ROW, "")])

    command.upgrade(alembic_config, "head")

    with engine.connect() as conn:
        got = conn.execute(text("SELECT name, channel_id FROM gridworks.reading_channels ORDER BY name")).all()
    assert got == [("vdc-relay", LAYOUT_ID), ("vdc-relay-state", None), ("vdc-relay1", LAYOUT_ID)]


def test_uncovered_data_row_fails_loud(before_state, alembic_config, engine):
    with engine.connect() as conn:
        insert_row(conn, UNCOVERED_ROW, "hp-lwt", "data.channel.gt")
        conn.commit()
    write_map(before_state, [(OLD_NAME_ROW, LAYOUT_ID), (NEW_NAME_ROW, LAYOUT_ID)])

    with pytest.raises(RuntimeError, match="1 reading_channels rows are not in the channel_id map"):
        command.upgrade(alembic_config, "head")


def test_downgrade_drops_the_column(before_state, alembic_config, engine):
    write_map(before_state, [(OLD_NAME_ROW, LAYOUT_ID), (NEW_NAME_ROW, LAYOUT_ID)])
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, BEFORE)
    with engine.connect() as conn:
        cols = {r.column_name for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema='gridworks' AND table_name='reading_channels'"))}
    assert "channel_id" not in cols
    command.upgrade(alembic_config, "head")
