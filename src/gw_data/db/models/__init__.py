"""List of all the models"""

from gw_data.db.models.position_point import PositionPointSql
from gw_data.db.models.g_node import GNodeSql
from gw_data.db.models.connectivity_edge import ConnectivityEdgeSql

from gw_data.db.models.customer import CustomerSql
from gw_data.db.models.installer import InstallerSql
from gw_data.db.models.user import UserSql
from gw_data.db.models.installation import InstallationSql
from gw_data.db.models.user_installation_role import UserInstallationRoleSql

from gw_data.db.models.reading_channel import ReadingChannelSql
from gw_data.db.models.message import MessageSql
from gw_data.db.models.reading import ReadingSql


# import position_point
# import g_node
# import connectivity_edge
# import customer
# import installer
# import user
# import data_channel
# import message
# import reading
__all__ = [
    "PositionPointSql",
    "GNodeSql",
    "ConnectivityEdgeSql",
    "CustomerSql",
    "InstallerSql",
    "UserSql",
    "InstallationSql",
    "UserInstallationRoleSql",
    "ReadingChannelSql",
    "MessageSql",
    "ReadingSql"
]
