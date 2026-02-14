# Gridworks Db Models

Put stuff in here about:
- Uuids for PKs
- Dates/times in the DB and ASL

## Database Setup

Workflow:

1. Run the _XX_drop_all.sql
2. Run 0_server_init.sql
3. Recreate alembic migrations
4. Add the following custom SQL:
```
    op.execute("SELECT create_hypertable('messages', by_range('timestamp'))")
    op.execute("SELECT create_hypertable('readings', by_range('timestamp'))")
    op.execute("""
        ALTER TABLE readings SET(
            timescaledb.enable_columnstore, 
            timescaledb.orderby = 'timestamp DESC', 
            timescaledb.segmentby = 'data_channel_id')
    """)
```

```
    op.execute('DROP TYPE base_g_node_class')
    op.execute('DROP TYPE g_node_status')
    op.execute('DROP TYPE connectivity_edge_status')
```


The recommended setup is as follows:

### 1. Install PostgreSQL with TimescaleDB on a Docker image.

Detailed instructions for this are online at: 
https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker

A few things to note:
* Install the `latest/pg-18` version of the Docker image.
* When building the container, you need to include a port mapping for 5432. If you are not already running a PostgreSQL instance on your machine than you can just map `5432:5432`. But if you are already running PostgreSQL (either with Docker or natively) you will need to select a different port (e.g. `5433:5432`). Whichever port you choose will need to be in the `GW_DB_URL` value in your `.env` file.
* When building the container, you need to include a `POSTGRES_PASSWORD` env variable, which will be the password for the default `postgres` user.




SQLAlchemy models for the GridNodeRegistry.

Each SQL row corresponds to a serialized ASL GT snapshot.
ASL types are used for validation (via the codec) before any insert/update.



```

## Requirements

Python version requirement: 3.12.x
Reason: SQLAlchemy/Alembic/Postgres driver stability and CI reproducibility.

## Configuration & Secrets 

Gridworks Db Models uses `pydantic-settings` for runtime configuration.

All configuration is loaded through the `Settings` class:
```
from gw_data.settings import Settings
import dotenv

settings = Settings(_env_file=dotenv.find_dotenv())
```
By default, all variables are loaded from a .env file in the project root.
To get started:

 1. Copy the provided template:
```
cp template.env .env
```
 2. Edit the `.env` file to include your database credentials and any overrides.


## Database change management

Using alembic for change managmenet. E.g.

```
uv run alembic revision --autogenerate -m "description e.g. initial schema"
uv run alembic upgrade head
```
## Logs
By default, logs should be written to
```
~/.local/state/gridworks/GW_DATA/log/
```
This follows the GridWorks convention.

## Next steps.
  0. Set up a dev environment for postgres and then use alembic to generate
  the table.
    - I tried setting up docker-compose.yaml but the postgres roles were failing.
  1. Add history tables 
  2. Enforce core invariants that aren't caught by ASL
     - Alias Uniqueness through time
     - Active GNode tree must be parent-closed
     - Active physical GNode subtree must be parent-closed
     - **ConnectivityEdge consistency** GNodeIds and Aliases match
     - **ConnectivityEdge coverage**
   That is, For every non-root physical GNode with alias A:

```
For every non-root GNode with alias A:
    Let P = parent alias of A
    The registry MUST contain exactly one ConnectivityEdge
    with FromGNodeId = <UUID(P)> AND ToGNodeId = <UUID(A)>
```

 3. Manage lifecycle states
    - **GNodeStatus**
       - Pending -> Active only
       - Active -> {Suspended, PermanentlyDeactivated}
       - Suspended -> {Active, PermanentlyDeactivated}
       - PermanentlyDeactivated -> no change
    - **BaseGNodeClass**  ConnectivityNode <-> MarketMaker 
 4. Implement API Endpoints (FastAPI)
 5. Set up tests & CI