"""house_operating_status: the current operating status of each house

One row per TerminalAsset, keyed on its GNodeId, holding the latest
gw.house.operating.status word the journal has for it verbatim, with the
scada alias, the word's name and version, the journaled message it came
from, the sender's clock and who produced the row (the scada, or gjk
deriving it for a house whose scada does not send the word). A reader asks
for a house's status by key instead of scanning the messages hypertable.
gjk is the writer.

Revision ID: d4a7c9e1b2f3
Revises: b7d2e4f6a8c1
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4a7c9e1b2f3"
down_revision: Union[str, Sequence[str], None] = "b7d2e4f6a8c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "gridworks"
TABLE = "house_operating_status"
INDEX = "ix_gridworks_house_operating_status_terminal_asset_alias"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("ta_g_node_id", sa.Uuid(), nullable=False),
        sa.Column("terminal_asset_alias", sa.String(), nullable=False),
        sa.Column("scada_alias", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("type_name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "persisted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ta_g_node_id"),
        schema=SCHEMA,
    )
    op.create_index(INDEX, TABLE, ["terminal_asset_alias"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index(INDEX, table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
