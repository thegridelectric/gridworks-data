"""An ephemeral TimescaleDB (testcontainers) for the migration tests.

The chain is run by alembic exactly as it is on journaldb, from an empty
database with the `timescaledb` extension and the `gridworks` schema,
which `scripts/0_db_create.psql` and `2_db_schema_setup.sql` provide in
deploy. Set `GW_DATA_TEST_PG_URL` to use an already-running TimescaleDB
instead; without either, the tests self-skip.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from alembic.config import Config

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "timescale/timescaledb-ha:pg18-ts2.25"

# The testcontainers reaper bind-mounts the Docker socket, which Docker
# Desktop on macOS refuses. The fixture stops its own container.
os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")


@pytest.fixture(scope="session")
def pg_url():
    override = os.environ.get("GW_DATA_TEST_PG_URL")
    if override:
        yield override
        return
    try:
        from testcontainers.community.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers not installed")
    try:
        pg = PostgresContainer(IMAGE, driver="psycopg", username="gw_admin", password="gw_admin", dbname="tsdb")
        pg.start()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"could not start a testcontainers TimescaleDB: {e}")
    try:
        url = pg.get_connection_url()
        eng = create_engine(url, isolation_level="AUTOCOMMIT")
        with eng.connect() as c:
            c.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            c.execute(text("CREATE SCHEMA IF NOT EXISTS gridworks"))
            # The roles the migrations grant to, as 1_db_user_setup.psql creates them.
            for role in ("gw_journalkeeper", "gw_visualizer", "gw_alerts", "gw_analyst"):
                c.execute(text(f"CREATE ROLE {role}"))
        eng.dispose()
        yield url
    finally:
        pg.stop()


@pytest.fixture(scope="session")
def alembic_config(pg_url) -> Config:
    # alembic/env.py builds its URL from Settings (GW_DATA_DB_URL).
    os.environ["GW_DATA_DB_URL"] = pg_url
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    return cfg


@pytest.fixture(scope="session")
def engine(pg_url):
    eng = create_engine(pg_url, future=True)
    yield eng
    eng.dispose()
