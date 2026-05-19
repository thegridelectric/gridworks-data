import csv
import dotenv
import json
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
from gw_data.db.models import GNodeSql, CustomerSql, InstallerSql, InstallationSql


dotenv.load_dotenv()
settings = Settings()
engine = create_engine(settings.db_url.get_secret_value(), echo=True)

db_sessionmaker = sessionmaker(bind=engine)
db_session = db_sessionmaker()

default_installer = InstallerSql(
    id = uuid.uuid4(),
    info = json.dumps({
        "company_name": "Millinocket Heating Installers"
    })
)
db_session.add(default_installer)

beech_id = None
file_path = os.path.join(os.path.dirname(__file__), './seed_data/homes.csv')
with open(file_path, newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(csv_reader) # Skip the header row
    for row in csv_reader:
        # "short_alias","address","primary_contact","secondary_contact","hardware_layout","unique_id","g_node_alias","alert_status","representation_status","scada_ip_address","scada_git_commit","house_parameters","created_at"
        (short_alias, address_json, primary_contact_json, secondary_contact_json, hardware_layout_json, unique_id, g_node_alias, alert_status_json, representation_status_json, scada_ip_address, scada_git_commit, house_parameters_json, created_at) = row

        g_node = GNodeSql(
            id = uuid.uuid4(),
            alias = g_node_alias,
            base_class = None,
            g_node_class = BaseGNodeClass.LeafTransactiveNode,
            status = GNodeStatus.Active,
            display_name = None,
            created_at = created_at
        )
        db_session.add(g_node)

        customer = CustomerSql(
            id = uuid.uuid4(),
            primary_contact = json.loads(primary_contact_json),
            secondary_contact = json.loads(secondary_contact_json),
        )
        db_session.add(customer)

        installation = InstallationSql(
            id = uuid.uuid4(),
            g_node_id = g_node.id,
            display_name = short_alias,
            customer_id = customer.id,
            installer_id = default_installer.id,
            address = json.loads(address_json),
            alert_status = json.loads(alert_status_json),
            hardware_layout = json.loads(hardware_layout_json),
            representation_status = json.loads(representation_status_json),
            house_parameters = json.loads(house_parameters_json),
            scada_ip_address = scada_ip_address,
            scada_git_commit = scada_git_commit
        )    

        if installation.display_name == 'beech':
            beech_id = installation.id

        db_session.add(installation)


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
    installation_id = beech_id
))

db_session.commit()
