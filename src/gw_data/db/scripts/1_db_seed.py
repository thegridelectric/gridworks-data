import csv
import dotenv
import json
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
        "company_name": "Paul Moscone's Heating Sales And Service"
    })
)
db_session.add(default_installer)

with open('seed_data/homes.csv', newline='') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(csv_reader) # Skip the header row
    for row in csv_reader:
        # "short_alias","address","primary_contact","secondary_contact","hardware_layout","unique_id","g_node_alias","alert_status","representation_status","scada_ip_address","scada_git_commit","house_parameters","created_at"
        (short_alias, address, primary_contact, secondary_contact, hardware_layout, unique_id, g_node_alias, alert_status, representation_status, scada_ip_address, scada_git_commit, house_parameters, created_at) = row

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
            primary_contact = primary_contact,
            secondary_contact = secondary_contact,
        )
        db_session.add(customer)

        installation = SpaceheatInstallationSql(
            id = uuid.uuid4(),
            g_node_id = g_node.id,
            display_name = short_alias,
            customer_id = customer.id,
            installer_id = default_installer.id,
            address = address,
            alert_status = alert_status,
            hardware_layout = hardware_layout,
            representation_status = representation_status,
            house_parameters = house_parameters,
            scada_ip_address = scada_ip_address,
            scada_git_commit = scada_git_commit
        )    
        db_session.add(installation)


    db_session.commit()
