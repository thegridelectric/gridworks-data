import csv
import dotenv
import os
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from getpass import getpass
from passlib.context import CryptContext

from gw_data.config import Settings
from gw_data.db.models.user import UserSql
from gw_data.db.models.user_installation_role import UserInstallationRoleSql
from gw_data.sema.enums import BaseGNodeClass, GNodeStatus
from gw_data.db.models import GNodeSql


dotenv.load_dotenv()
settings = Settings()
engine = create_engine(settings.db_url.get_secret_value(), echo=True)

db_sessionmaker = sessionmaker(bind=engine)
db_session = db_sessionmaker()

beech_ta_id = None
file_path = os.path.join(os.path.dirname(__file__), './seed_data/homes.csv')
with open(file_path, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(csv_reader) # Skip the header row
    for row in csv_reader:
        # "short_alias","address","primary_contact","secondary_contact","hardware_layout","unique_id","g_node_alias","alert_status","representation_status","scada_ip_address","scada_git_commit","house_parameters","created_at"
        # Only the aliases are used: the house is a pair of registry nodes, the
        # LeafTransactiveNode and its TerminalAsset. Nothing about a person is seeded.
        (short_alias, _address, _primary, _secondary, _layout, _unique_id, g_node_alias, _alert, _repr, _ip, _commit, _params, created_at) = row

        ltn = GNodeSql(
            id = uuid.uuid4(),
            alias = g_node_alias,
            base_class = None,
            g_node_class = BaseGNodeClass.LeafTransactiveNode,
            status = GNodeStatus.Active,
            display_name = None,
            created_at = created_at
        )
        ta = GNodeSql(
            id = uuid.uuid4(),
            alias = g_node_alias + ".ta",
            base_class = None,
            g_node_class = BaseGNodeClass.TerminalAsset,
            status = GNodeStatus.Active,
            display_name = short_alias.title() + " TerminalAsset",
            created_at = created_at
        )
        db_session.add(ltn)
        db_session.add(ta)
        if short_alias == 'beech':
            beech_ta_id = ta.id


gbo_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)


admin_pw = None
while admin_pw is None:
    admin_pw = getpass('Enter a password for the user "admin":')
    admin_pw_confirmed = getpass('Enter again to confirm:')
    if admin_pw != admin_pw_confirmed:
        admin_pw = None

admin = UserSql(
    id = uuid.uuid4(),
    username = "admin",
    hashed_password = gbo_pwd_context.hash(admin_pw)
)
db_session.add(admin)

beech_user_pw = None
while beech_user_pw is None:
    beech_user_pw = getpass('Enter a password for the user "beech-user":')
    beech_user_pw_confirmed = getpass('Enter again to confirm:')
    if beech_user_pw != beech_user_pw_confirmed:
        beech_user_pw = None

beech_user = UserSql(
    id = uuid.uuid4(),
    username = "beech-user",
    hashed_password = gbo_pwd_context.hash(beech_user_pw)
)
db_session.add(beech_user)

db_session.add(UserInstallationRoleSql(
    user_id = admin.id,
    role = "admin"
))

db_session.add(UserInstallationRoleSql(
    user_id = beech_user.id,
    role = "owner",
    ta_g_node_id = beech_ta_id
))

db_session.commit()
