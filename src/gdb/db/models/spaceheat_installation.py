from __future__ import annotations

from sqlalchemy import (
    String,
    Integer,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from gdb.db.models._base import Base
from gdb.db.models.customer import CustomerSql
from gdb.db.models.installer import InstallerSql

class SpaceheatInstallationSql(Base):
    __tablename__ = "spaceheat_installations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    g_node_id: Mapped[str] = mapped_column(
        ForeignKey("g_nodes.id"),
        nullable=False
    )
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False
    )
    customer: Mapped[CustomerSql] = relationship()

    installer_id: Mapped[str] = mapped_column(
        ForeignKey("installers.id"),
        nullable=False
    )
    installer: Mapped[InstallerSql] = relationship()

    address: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    alert_status: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    hardware_layout: Mapped[JSONB] = mapped_column(JSONB, nullable=False)
    representation_status: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    house_parameters: Mapped[JSONB] = mapped_column(JSONB, nullable=True)
    scada_ip_address: Mapped[str] = mapped_column(String, nullable=True)
    scada_git_commit: Mapped[str] = mapped_column(String, nullable=True)

