"""The house_operating_status migration: one current status row per
terminal asset, keyed on the GNodeId, upserted, and dropped on downgrade."""

import json
import uuid

from alembic import command
from sqlalchemy import inspect, text

BEFORE = "b7d2e4f6a8c1"
TABLE = "house_operating_status"
TA = uuid.uuid4()


def test_one_row_per_terminal_asset(alembic_config, engine):
    # From wherever the session left the chain: to head, then back below this migration.
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, BEFORE)
    assert TABLE not in inspect(engine).get_table_names(schema="gridworks")

    command.upgrade(alembic_config, "head")
    with engine.connect() as conn:
        for source, created_at in (("derived", "2026-10-21T12:00:00Z"), ("scada", "2026-10-21T13:00:00Z")):
            conn.execute(
                text(
                    f"INSERT INTO gridworks.{TABLE} (ta_g_node_id, terminal_asset_alias, scada_alias, source, type_name, version, payload, created_at) "
                    "VALUES (:ta, 'hw1.isone.me.versant.keene.beech.ta', 'hw1.isone.me.versant.keene.beech.scada', :source, 'gw.house.operating.status', '000', :payload, :created_at) "
                    "ON CONFLICT (ta_g_node_id) DO UPDATE SET payload = EXCLUDED.payload, source = EXCLUDED.source, created_at = EXCLUDED.created_at"
                ),
                {"ta": TA, "source": source, "payload": json.dumps({"CreatedMs": created_at}), "created_at": created_at},
            )
        conn.commit()
        rows = conn.execute(text(f"SELECT ta_g_node_id, source, payload->>'CreatedMs' FROM gridworks.{TABLE}")).all()
    assert rows == [(TA, "scada", "2026-10-21T13:00:00Z")]


def test_downgrade_drops_the_table(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, BEFORE)
    assert TABLE not in inspect(engine).get_table_names(schema="gridworks")
    command.upgrade(alembic_config, "head")
