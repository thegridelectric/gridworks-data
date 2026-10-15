"""retire installations: the customer tables leave journaldb

installations, customers and installers are dropped. Customer contact
data and addresses live in the private customer store, keyed by the
TerminalAsset GNodeId; the engineering and ops copies that had grown onto
installations (layout, house parameters, representation and alert
status, scada address and commit) are deleted, not moved: the journal's
words hold the first two and the rest belong elsewhere.

user_installation_roles re-keys from installation_id to ta_g_node_id, a
plain UUID with no foreign key. The data step maps each role's
installation to its TerminalAsset through the g_nodes projection:
installations.g_node_id is the house's LeafTransactiveNode, and the
TerminalAsset is the node whose alias is the LTN's alias plus ".ta".
A role whose installation cannot be mapped fails the migration rather
than losing its house. Null still means every house.

Revision ID: e5a1c2d3f4b6
Revises: c3e8f1a9d2b7
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5a1c2d3f4b6"
down_revision: Union[str, Sequence[str], None] = "c3e8f1a9d2b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "gridworks"


def upgrade() -> None:
    op.add_column(
        "user_installation_roles",
        sa.Column("ta_g_node_id", sa.Uuid(), nullable=True),
        schema=SCHEMA,
    )
    op.execute(
        f"""
        UPDATE {SCHEMA}.user_installation_roles r
        SET ta_g_node_id = ta.id
        FROM {SCHEMA}.installations i
        JOIN {SCHEMA}.g_nodes ltn ON ltn.id = i.g_node_id
        JOIN {SCHEMA}.g_nodes ta ON ta.alias = ltn.alias || '.ta'
        WHERE r.installation_id = i.id
        """
    )
    unmapped = op.get_bind().execute(
        sa.text(
            f"SELECT count(*) FROM {SCHEMA}.user_installation_roles "
            "WHERE installation_id IS NOT NULL AND ta_g_node_id IS NULL"
        )
    ).scalar()
    if unmapped:
        raise RuntimeError(
            f"{unmapped} user_installation_roles row(s) name an installation "
            "with no TerminalAsset in g_nodes; add the TA rows first"
        )
    op.drop_constraint(
        "user_installation_roles_installation_id_fkey",
        "user_installation_roles",
        schema=SCHEMA,
        type_="foreignkey",
    )
    op.drop_constraint(
        "user_installation_roles_user_installation_key",
        "user_installation_roles",
        schema=SCHEMA,
        type_="unique",
    )
    op.drop_column("user_installation_roles", "installation_id", schema=SCHEMA)
    op.create_unique_constraint(
        "user_installation_roles_user_ta_key",
        "user_installation_roles",
        ["user_id", "ta_g_node_id"],
        schema=SCHEMA,
    )
    op.drop_table("installations", schema=SCHEMA)
    op.drop_table("customers", schema=SCHEMA)
    op.drop_table("installers", schema=SCHEMA)


def downgrade() -> None:
    """Restores the tables empty and the roles column null: the customer
    data is not in this database to put back."""
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("primary_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("secondary_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_table(
        "installers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("info", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_table(
        "installations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("g_node_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("installer_id", sa.Uuid(), nullable=False),
        sa.Column("address", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("alert_status", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hardware_layout", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("representation_status", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("house_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("scada_ip_address", sa.String(), nullable=True),
        sa.Column("scada_git_commit", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], [f"{SCHEMA}.customers.id"]),
        sa.ForeignKeyConstraint(["g_node_id"], [f"{SCHEMA}.g_nodes.id"]),
        sa.ForeignKeyConstraint(["installer_id"], [f"{SCHEMA}.installers.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.drop_constraint(
        "user_installation_roles_user_ta_key",
        "user_installation_roles",
        schema=SCHEMA,
        type_="unique",
    )
    op.drop_column("user_installation_roles", "ta_g_node_id", schema=SCHEMA)
    op.add_column(
        "user_installation_roles",
        sa.Column("installation_id", sa.Uuid(), nullable=True),
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "user_installation_roles_installation_id_fkey",
        "user_installation_roles",
        "installations",
        ["installation_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
    )
    op.create_unique_constraint(
        "user_installation_roles_user_installation_key",
        "user_installation_roles",
        ["user_id", "installation_id"],
        schema=SCHEMA,
    )
