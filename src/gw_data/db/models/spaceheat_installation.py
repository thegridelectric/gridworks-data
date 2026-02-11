from __future__ import annotations
import uuid

from sqlalchemy import (
    String,
    Uuid,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from gw_data.db.models._base import Base
from gw_data.db.models.customer import CustomerSql
from gw_data.db.models.installer import InstallerSql

class SpaceheatInstallationSql(Base):
    __tablename__ = "spaceheat_installations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
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

