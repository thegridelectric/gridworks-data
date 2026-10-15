import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from gw_data.db.models._base import Base


class UserInstallationRoleSql(Base):
    """What a dashboard login may do, and for which house.

    `ta_g_node_id` is the house's TerminalAsset GNodeId, an opaque id with
    no foreign key: the registry owns the node and the private customer
    store owns the household behind it. Null means every house.
    """

    __tablename__ = "user_installation_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    ta_g_node_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "ta_g_node_id", name="user_installation_roles_user_ta_key"),
    )

    # This table does not need a true primary key -- but SQLAlchemy requires one.
    # So we define a synthetic PK out of two columns that should always be unique.
    __mapper_args__ = {
        "primary_key": [user_id, ta_g_node_id]
    }
