"""The layouts migration: one current layout row per terminal asset,
keyed on the GNodeId, and the model agrees with the result."""

import json
import uuid

from alembic import command
from sqlalchemy import inspect, text

BEFORE = "e5a1c2d3f4b6"
TA = uuid.uuid4()


def test_layouts_table_holds_one_row_per_terminal_asset(alembic_config, engine):
    command.upgrade(alembic_config, BEFORE)
    assert "layouts" not in inspect(engine).get_table_names(schema="gridworks")

    command.upgrade(alembic_config, "head")
    with engine.connect() as conn:
        for sent_at in ("2026-10-20T12:00:00Z", "2026-10-20T13:00:00Z"):
            conn.execute(
                text(
                    "INSERT INTO gridworks.layouts (ta_g_node_id, terminal_asset_alias, from_alias, type_name, version, payload, sent_at) "
                    "VALUES (:ta, 'hw1.isone.me.versant.keene.beech.ta', 'hw1.isone.me.versant.keene.beech.scada', 'layout.lite', '012', :payload, :sent_at) "
                    "ON CONFLICT (ta_g_node_id) DO UPDATE SET payload = EXCLUDED.payload, sent_at = EXCLUDED.sent_at"
                ),
                {"ta": TA, "payload": json.dumps({"SentAt": sent_at}), "sent_at": sent_at},
            )
        conn.commit()
        rows = conn.execute(text("SELECT ta_g_node_id, version, payload->>'SentAt' FROM gridworks.layouts")).all()
    assert rows == [(TA, "012", "2026-10-20T13:00:00Z")]


def test_downgrade_drops_layouts(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, BEFORE)
    assert "layouts" not in inspect(engine).get_table_names(schema="gridworks")
    command.upgrade(alembic_config, "head")
