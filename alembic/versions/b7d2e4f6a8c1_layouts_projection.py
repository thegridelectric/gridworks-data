"""layouts: the current layout of each terminal asset

One row per TerminalAsset, keyed on its GNodeId, holding the latest layout
word the journal has seen for it verbatim, with the sender, the word's
name and version, the journaled message it came from and the sender's
clock. A reader asks for a house's layout by key instead of scanning the
messages hypertable for the newest layout message. gjk is the writer.

Revision ID: b7d2e4f6a8c1
Revises: e5a1c2d3f4b6
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d2e4f6a8c1"
down_revision: Union[str, Sequence[str], None] = "e5a1c2d3f4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "gridworks"


def upgrade() -> None:
    op.create_table(
        "layouts",
        sa.Column("ta_g_node_id", sa.Uuid(), nullable=False),
        sa.Column("terminal_asset_alias", sa.String(), nullable=False),
        sa.Column("from_alias", sa.String(), nullable=False),
        sa.Column("type_name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "persisted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("ta_g_node_id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_gridworks_layouts_terminal_asset_alias",
        "layouts",
        ["terminal_asset_alias"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_gridworks_layouts_terminal_asset_alias", table_name="layouts", schema=SCHEMA)
    op.drop_table("layouts", schema=SCHEMA)
