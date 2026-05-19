import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gw_data.db.models._base import Base
from gw_data.db.models.installation import InstallationSql


class UserInstallationRoleSql(Base):
    __tablename__ = "user_installation_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    installation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("installations.id"),
        nullable=True
    )

    # A null installation_id associates the role to ALL installations (e.g. for admin users)
    installations: Mapped[list[InstallationSql]] = relationship(
        "InstallationSql",
        uselist=True,
        lazy="joined",
        primaryjoin="or_(InstallationSql.id==UserInstallationRoleSql.installation_id, UserInstallationRoleSql.installation_id == None)"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "installation_id", name="user_installation_roles_user_installation_key"),
    )

    # This table does not need a true primary key -- but SQLAlchemy requires one.
    # So we define a synthetic PK out of two columns that should always be unique. 
    __mapper_args__ = {
        "primary_key": [user_id, installation_id]
    }
