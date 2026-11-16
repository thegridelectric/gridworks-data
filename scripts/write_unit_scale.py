"""Rewrite gridworks.unit_scale from the vendored sema snapshot.

Run after `scripts/regen_sema_snapshot.sh` changes either unit enum:

    GW_DATA_DB_URL=<admin url> uv run python scripts/write_unit_scale.py

The migration that creates the table fills it the same way; this is the
re-run for a table that already exists. Prints the row count.
"""

from sqlalchemy import create_engine

from gw_data.config import Settings
from gw_data.db.unit_scale import write_unit_scale


def main() -> None:
    engine = create_engine(Settings().db_url.get_secret_value())
    with engine.begin() as conn:
        n = write_unit_scale(conn)
    print(f"gridworks.unit_scale: {n} rows")


if __name__ == "__main__":
    main()
