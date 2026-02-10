from __future__ import annotations

from sqlalchemy import (
    String,
    ForeignKey
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from gdb.db.models._base import Base

class SpaceheatInstallationSql(Base):
    __tablename__ = "spaceheat_installations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    g_node_id: Mapped[str] = mapped_column(
        ForeignKey("g_nodes.id"),
        nullable=False
    )
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False
    )
    installer_id: Mapped[str] = mapped_column(
        ForeignKey("installers.id"),
        nullable=False
    )
