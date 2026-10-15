"""The retire-installations migration on a database shaped like journaldb
before it: roles re-key to the TerminalAsset, the three tables go, and the
models agree with the result."""

import uuid

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

import gw_data.db.models  # noqa: F401  (registers every model on Base)
from gw_data.db.models._base import Base

BEFORE = "c3e8f1a9d2b7"
LTN = uuid.uuid4()
TA = uuid.uuid4()
INSTALLATION = uuid.uuid4()
ADMIN = uuid.uuid4()
OWNER = uuid.uuid4()


def fill_before_state(conn) -> None:
    conn.execute(
        text(
            "INSERT INTO gridworks.g_nodes (id, alias, base_class, g_node_class, status, created_at) VALUES "
            "(:ltn, 'hw1.isone.me.versant.keene.beech', 'LeafTransactiveNode', 'LeafTransactiveNode', 'Active', now()), "
            "(:ta, 'hw1.isone.me.versant.keene.beech.ta', 'TerminalAsset', 'TerminalAsset', 'Pending', now())"
        ),
        {"ltn": LTN, "ta": TA},
    )
    cust, inst = uuid.uuid4(), uuid.uuid4()
    conn.execute(text("INSERT INTO gridworks.customers VALUES (:id, '{}', '{}')"), {"id": cust})
    conn.execute(text("INSERT INTO gridworks.installers VALUES (:id, '\"x\"')"), {"id": inst})
    conn.execute(
        text(
            "INSERT INTO gridworks.installations (id, g_node_id, display_name, customer_id, installer_id, address, alert_status, hardware_layout) "
            "VALUES (:id, :ltn, 'beech', :c, :i, '{}', '{}', '{}')"
        ),
        {"id": INSTALLATION, "ltn": LTN, "c": cust, "i": inst},
    )
    conn.execute(
        text(
            "INSERT INTO gridworks.users (id, username, hashed_password, is_active, created_at, updated_at) VALUES "
            "(:a, 'admin', 'x', true, now(), now()), (:o, 'beech-user', 'x', true, now(), now())"
        ),
        {"a": ADMIN, "o": OWNER},
    )
    conn.execute(
        text(
            "INSERT INTO gridworks.user_installation_roles (user_id, role, installation_id) VALUES "
            "(:a, 'admin', NULL), (:o, 'owner', :inst)"
        ),
        {"a": ADMIN, "o": OWNER, "inst": INSTALLATION},
    )
    conn.commit()


def test_roles_rekey_and_tables_drop(alembic_config, engine):
    command.upgrade(alembic_config, BEFORE)
    with engine.connect() as conn:
        fill_before_state(conn)

    command.upgrade(alembic_config, "head")

    with engine.connect() as conn:
        roles = conn.execute(
            text("SELECT u.username, r.role, r.ta_g_node_id FROM gridworks.user_installation_roles r JOIN gridworks.users u ON u.id = r.user_id ORDER BY 1")
        ).all()
    assert roles == [("admin", "admin", None), ("beech-user", "owner", TA)]
    tables = set(inspect(engine).get_table_names(schema="gridworks"))
    assert not ({"installations", "customers", "installers"} & tables)
    assert "installation_id" not in {c["name"] for c in inspect(engine).get_columns("user_installation_roles", schema="gridworks")}


def test_models_match_head(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn,
            opts={
                "include_schemas": True,
                "version_table_schema": "gridworks",
                "include_name": lambda name, type_, parent: (name == "gridworks") if type_ == "schema" else (name not in ("cached_hourly_data",) if type_ == "table" else True),
            },
        )
        diff = compare_metadata(ctx, Base.metadata)
    # Hypertables and the continuous aggregate add indexes of their own; only table-level drift matters here.
    table_diffs = [d for d in diff if d[0] in ("add_table", "remove_table", "add_column", "remove_column", "add_constraint", "remove_constraint")]
    assert table_diffs == [], table_diffs


def test_downgrade_restores_empty_tables(alembic_config, engine):
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, BEFORE)
    tables = set(inspect(engine).get_table_names(schema="gridworks"))
    assert {"installations", "customers", "installers"} <= tables
    command.upgrade(alembic_config, "head")
