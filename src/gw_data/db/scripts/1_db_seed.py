import csv
import dotenv
import json
import os
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gw_data.config import Settings
from gw_data.asl.enums.base_g_node_class import BaseGNodeClass
from gw_data.asl.enums.g_node_status import GNodeStatus
from gw_data.db.models import GNodeSql, CustomerSql, InstallerSql, SpaceheatInstallationSql


dotenv.load_dotenv()
settings = Settings()
engine = create_engine(settings.db_url.get_secret_value())

db_sessionmaker = sessionmaker(bind=engine)
db_session = db_sessionmaker()

default_installer = InstallerSql(
    id = uuid.uuid4(),
    info = json.dumps({
        "company_name": "Millinocket Heating Installers"
    })
)
db_session.add(default_installer)

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

        installation = SpaceheatInstallationSql(
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
        db_session.add(installation)


    db_session.commit()
