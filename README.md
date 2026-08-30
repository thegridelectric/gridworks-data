# Gridworks Data

This project contains code related to working with databases in the GridWorks ecosystem.

Our platform is PostgreSQL, with the TimescaleDB (+toolkit) extensions for efficiently handling time-series data.

## Prerequisites

* **Docker Engine** — to run PostgreSQL+TimescaleDB locally.
  (If you have previously set up the RabbitMQ server from `gridworks-base`, you should already have Docker.)
* **`psql`** PostgreSQL command-line client (any modern version; tested with 14.x and 18.x).
  Install via your package manager (e.g. `brew install libpq && brew link --force libpq` on macOS, `sudo apt install postgresql-client` on Linux). Check with `psql --version`.
  *(Optional: `pgAdmin` as a GUI for inspecting the database.)*
* **Python ≥ 3.12** and `uv` (per the rest of the GridWorks toolchain).

## Database Setup

The following steps will get you set up to run with the database, either locally or on a managed Tiger Cloud instance.

### Local Pre-requisite: PostgreSQL+TimescaleDB container

If running locally, you'll need to start by pulling the official TimescaleDB image and starting a container. **You need the `-ha` variant** for PostgreSQL v18 and TimescaleDB v2.25 — without `-ha` you'll get the "lite" version of TimescaleDB which is missing required functionality.

If you don't already have a PostgreSQL listener on port 5432, map `5432:5432`. If you do (native install, or another Docker postgres), pick a free port and map `<HOST_PORT>:5432` instead (e.g. `5433:5432`).

Pick a `POSTGRES_PASSWORD` — this becomes the password for the built-in `postgres` superuser; record it locally (e.g. in `.env`), don't commit it.

Concrete `docker run` example (uses 5433 and a placeholder password):

    docker run -d \
      --name gw-data-pg \
      -e POSTGRES_PASSWORD=changeme \
      -p 5433:5432 \
      timescale/timescaledb-ha:pg18-ts2.25

Verify the container is healthy: `docker ps` should show it up, and `PGPASSWORD=changeme psql -h 127.0.0.1 -p 5433 -U postgres -c "SELECT version();"` should return PostgreSQL 18.x.

Detailed instructions and alternative configurations: https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker

### Database Setup

This repo includes a numbered sequence of scripts in the `src/gw_data/db/scripts` folder that will get you up and running.

#### 0. (Local-Only) Create the Database

This step is not required (or even possible) on a Tiger Cloud managed server.

Run `0_db_create.sql` as the `postgres` user to create the `tsdb` database and add the `timescaledb` extension.

    psql -d "postgresql://127.0.0.1:<PORT>/" -U postgres -f src/gw_data/db/scripts/0_server_init.psql

* Replace `<PORT>` with the host port you mapped to 5432 (e.g. `5433`).
* You'll be prompted for the `postgres` user password (i.e., the one you previously set as `POSTGRES_PASSWORD` in your `docker run` command).

#### 1. Create the Users

Run `1_db_user_setup.psql` as follows to create the users we need. This script can be run as the `postgres` user locally, or the `tsdbadmin` user in Tiger Cloud.

    psql -d "postgresql://<SERVER>:<PORT>/" -U <postgres|tsdbadmin> -f src/gw_data/db/scripts/1_db_user_setup.psql

* Replace `<SERVER>` with the database server address (e.g., `127.0.0.1` when running locally).
* Again, replace `<PORT>` with your mapped host port.
* Again, you'll be prompted for the `postgres` user password.

This script creates five user roles, named by consumer: `gw_admin` (full ownership), `gw_journalkeeper` (insert/update/delete), and three select-only roles — `gw_visualizer` (the web API), `gw_alerts` (gwalert), `gw_analyst` (people and ad-hoc analysis) — with role-level statement timeouts (10 s for the two services, 2 min for the readers; long jobs use `SET LOCAL statement_timeout` per transaction).

**Note: the script uses `psql`'s interactive `\password` meta-command five times** (once for each user). It must be run **interactively** — it will prompt for each password as it runs and cannot be piped or run via CI:

You'll be prompted for new passwords for each of the users. Pick whatever you like and record them somewhere.

**Local dev convention: password = role name.** For the local container, run `1_db_user_setup_dev.psql` instead — it creates the same five roles non-interactively, each with password = role name (`gw_admin`/`gw_admin`, …):

    psql -d "postgresql://127.0.0.1:<PORT>/" -U postgres -f src/gw_data/db/scripts/1_db_user_setup_dev.psql

Consumers of this database (journalkeeper, gwalert, …) ship default `db_url`s that assume this convention, so a fresh checkout runs against the local container with no `.env`. Never use it on a shared or production server; the interactive script above is the production path.

**Reset shortcut:** if your local DB ever gets into a weird state, you can wipe it and start over with:

    psql -d "postgresql://127.0.0.1:<PORT>/" -U postgres -f src/gw_data/db/scripts/_XX_drop_all.sql

#### 2. Create the `gridworks` Schema

Run `2_db_schema_setup.sql` as follows to create our private `gridworks` schema and apply appropriate permissions. This should be run as the `gw_admin` user.

    psql -d "postgresql://<SERVER>:<PORT>/" -U gw_admin -f src/gw_data/db/scripts/2_db_schema_setup.psql

* Again, replace `<SERVER>` with the database server address.
* Again, replace `<PORT>` with your mapped host port.
* This time you'll be prompted for the `gw_admin` user password.

#### 3. Run the Alembic Migrations

Next we need to run the database migrations we've defined with Alembic to create the tables, etc. that we need.

But first we need to update our .env file. Copy `template.env` (at the repo root) to `.env`:

    cp template.env .env

Then, edit `.env` as follows:
* Replace `<SERVER>` with the database server address (e.g., `127.0.0.1` when running locally).
* Replace `<%PASSWORD%>` in `GW_DATA_DB_URL` with the `gw_admin` password you just set.
* Replace `<%PORT%>` with the host port you mapped to 5432 (e.g. `5433`).

Now we can run `3_db_alembic_upgrade.sh` as follows:

    `sh src/gw_data/db/scripts/3_db_alembic_upgrade.sh`

This should create 12 tables in the `gridworks` schema: `alembic_version`, `connectivity_edges`, `customers`, `g_nodes`, `installations`, `installers`, `messages`, `position_points`, `reading_channels`, `readings`, `user_installation_roles`, `users`.

Verify with `psql -d "postgresql://<SERVER>:<PORT>/tsdb" -U gw_admin -c "\dt gridworks.*"`.

#### 4. Seed the Database

With the database created, `gw_admin` ready, and `.env` filled in, you can seed some initial data:

    uv run python ./src/gw_data/db/scripts/1_db_seed.py

**Note: the seed script is also interactive** — it uses Python's `getpass` to prompt for passwords for two seeded users (`admin` and `beech-user`). It must be run from a real terminal (no piping). The seed populates a small set of dev users, a customer, an installation, and one g_node.

In the future we will have a more comprehensive seeding process that will ingest some actual message data.

## Best Practices for Databases

The following are some best practices that we should follow when at all possible:

* Primary Keys should be UUIDs, stored as the DB-native UUID type
* Dates/Times should be stored as `TIMESTAMPTZ`
* Migrations should be encouraged and done frequently to provide new functionality. Database schema is always temporary.
* Each application that uses that database should have its own dedicated user, with the minimal set of permissions. (In particular, `postgres` should never be used at all, and `gw_admin` should only be used for migrations and other tasks that require full ownership of the database.)

## TimescaleDB Performance

TimescaleDB does two main things to improve performance:
1. Separates time-series tables (which it calls "hypertables") into "chunks", each of which cover a certain timeframe.
2. Allows time-series data to be stored in column order with compression, which vastly improves performance for data that changes very little over time. This compression happens in a scheduled job, and only for data older than a configured threshold.

We have column-store compression enabled on the readings table for data older than 2 weeks, with compression segmented by the channel ID.

### Useful Queries

There are some useful queries listed in `useful-queries.sql` in the project root.
