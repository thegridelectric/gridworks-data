"""reading_channels.channel_id: the layout's channel Id as a column

A row's primary key is a surrogate; `channel_id` is the layout's channel
Id for the row's (terminal asset, name, unit), the lineage key that a
renamed channel's rows share and a unit change does not. NULL means no
layout Id names the pair: a state-machine pseudo row, or a unit that
history gave no Id of its own.

The data step applies a map (row id -> channel_id) built from tlayouts
and the journal's layout history by `scripts/channel_id_backfill_map.py`,
read from the csv named by GW_DATA_CHANNEL_ID_CSV, by default
`channel_id_backfill.csv` beside this file. A non-pseudo row the csv does
not cover fails the migration: regenerate the csv from the live table and
rerun.

Revision ID: f7c3d1a2b4e5
Revises: d4a7c9e1b2f3
"""

import csv
import os
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7c3d1a2b4e5"
down_revision: Union[str, Sequence[str], None] = "d4a7c9e1b2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "gridworks"
PSEUDO = "gjk.pseudo"
DEFAULT_CSV = Path(__file__).with_name("channel_id_backfill.csv")


def backfill_map() -> list[dict[str, str]]:
    path = Path(os.environ.get("GW_DATA_CHANNEL_ID_CSV", DEFAULT_CSV))
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return [{"id": r["id"], "channel_id": r["channel_id"] or None} for r in csv.DictReader(f)]


def upgrade() -> None:
    op.add_column(
        "reading_channels",
        sa.Column("channel_id", sa.Uuid(), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_reading_channels_channel_id",
        "reading_channels",
        ["channel_id"],
        schema=SCHEMA,
    )
    rows = backfill_map()
    conn = op.get_bind()
    if rows:
        conn.execute(
            sa.text(
                f"UPDATE {SCHEMA}.reading_channels SET channel_id = CAST(:channel_id AS uuid) WHERE id = CAST(:id AS uuid)"
            ),
            rows,
        )
    covered = {r["id"] for r in rows}
    uncovered = conn.execute(
        sa.text(
            f"SELECT id, terminal_asset_alias, name, unit FROM {SCHEMA}.reading_channels "
            f"WHERE channel_type <> '{PSEUDO}'"
        )
    ).all()
    uncovered = [r for r in uncovered if str(r.id) not in covered]
    if uncovered:
        sample = ", ".join(f"{r.terminal_asset_alias} {r.name} {r.unit}" for r in uncovered[:5])
        raise RuntimeError(
            f"{len(uncovered)} reading_channels rows are not in the channel_id map "
            f"(regenerate it from the live table with scripts/channel_id_backfill_map.py): {sample}"
        )


def downgrade() -> None:
    op.drop_index("ix_reading_channels_channel_id", table_name="reading_channels", schema=SCHEMA)
    op.drop_column("reading_channels", "channel_id", schema=SCHEMA)
