"""drop position_points: gw_data holds no position content

The analytics projection keeps only the registry's opaque
position_point_id (verbatim, no FK); location data lives with the
registry and the audit trail in the persistent store — neither plaintext
nor ciphertext coordinates belong here.

Revision ID: c3e8f1a9d2b7
Revises: a7f151e8163f
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e8f1a9d2b7"
down_revision: Union[str, Sequence[str], None] = "a7f151e8163f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "g_nodes_position_point_id_fkey",
        "g_nodes",
        schema="gridworks",
        type_="foreignkey",
    )
    op.drop_table("position_points", schema="gridworks")


def downgrade() -> None:
    op.create_table(
        "position_points",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("latitude_micro_deg", sa.Integer(), nullable=False),
        sa.Column("longitude_micro_deg", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="gridworks",
    )
    op.create_foreign_key(
        "g_nodes_position_point_id_fkey",
        "g_nodes",
        "position_points",
        ["position_point_id"],
        ["id"],
        source_schema="gridworks",
        referent_schema="gridworks",
    )
