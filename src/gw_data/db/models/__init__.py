"""List of all the models"""

from gw_data.db.models.g_node import GNodeSql
from gw_data.db.models.connectivity_edge import ConnectivityEdgeSql

from gw_data.db.models.user import UserSql
from gw_data.db.models.user_installation_role import UserInstallationRoleSql

from gw_data.db.models.reading_channel import ReadingChannelSql
from gw_data.db.models.message import MessageSql
from gw_data.db.models.reading import ReadingSql


__all__ = [
    "GNodeSql",
    "ConnectivityEdgeSql",
    "UserSql",
    "UserInstallationRoleSql",
    "ReadingChannelSql",
    "MessageSql",
    "ReadingSql"
]
