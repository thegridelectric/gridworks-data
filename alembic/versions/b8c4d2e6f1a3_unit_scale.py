"""unit_scale: what a reading's stored integer means, per unit enum value

One row per value of each unit enum the journal records as a channel's
unit_type: the gw1.quantity the unit measures, the base unit the integer
is a multiple of, and the scale. The hourly functions join on
(unit_type, unit) and select by channel name and quantity, so a channel
recorded in one enum and the same channel recorded in another read as
the same quantity. The rows come from the vendored sema snapshot through
gw_data.db.unit_scale, the table's only writer.

Revision ID: b8c4d2e6f1a3
Revises: f7c3d1a2b4e5
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from gw_data.db.unit_scale import write_unit_scale

# revision identifiers, used by Alembic.
revision: str = "b8c4d2e6f1a3"
down_revision: Union[str, Sequence[str], None] = "f7c3d1a2b4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "gridworks"
TABLE = "unit_scale"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("unit_type", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("quantity", sa.String(), nullable=False),
        sa.Column("base_unit", sa.String(), nullable=True),
        sa.Column("scale", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("unit_type", "unit"),
        schema=SCHEMA,
    )
    write_unit_scale(op.get_bind())


def downgrade() -> None:
    op.drop_table(TABLE, schema=SCHEMA)
