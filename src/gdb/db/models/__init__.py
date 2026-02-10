"""List of all the models"""

from gdb.db.models.position_point import PositionPointSql
from gdb.db.models.g_node import GNodeSql
from gdb.db.models.connectivity_edge import ConnectivityEdgeSql

from gdb.db.models.customer import CustomerSql
from gdb.db.models.installer import InstallerSql
from gdb.db.models.user import UserSql
from gdb.db.models.spaceheat_installation import SpaceheatInstallationSql

from gdb.db.models.data_channel import DataChannelSql
from gdb.db.models.message import MessageSql
from gdb.db.models.reading import ReadingSql


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
    "SpaceheatInstallationSql",
    "DataChannelSql",
    "MessageSql",
    "ReadingSql"
]
