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

The following steps will get you set up to run with the database.

### 1. Run a PostgreSQL+TimescaleDB container

Pull the official TimescaleDB image and start a container. **You need the `-ha` variant** for PostgreSQL v18 and TimescaleDB v2.25 — without `-ha` you'll get the "lite" version of TimescaleDB which is missing required functionality.

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

### 2. Create the Database

The repo ships an init script at `src/gw_data/db/scripts/0_server_init.psql` that creates the `gridworks` database and three roles: `gw_admin` (full ownership), `gw_writer` (insert/update/delete), and `gw_reader` (select-only).

**Note: the script uses `psql`'s interactive `\password` meta-command three times** (for `gw_admin`, `gw_writer`, `gw_reader`). It must be run **interactively** — it will prompt for each password as it runs and cannot be piped or run via CI:

    psql -d "postgresql://127.0.0.1:<PORT>/" -U postgres -f src/gw_data/db/scripts/0_server_init.psql

You'll be prompted first for the `postgres` superuser password (the one you set as `POSTGRES_PASSWORD` in §1), then in turn for new passwords for `gw_admin`, `gw_writer`, and `gw_reader`. Pick whatever you like and record them in your local `.env`.

For non-interactive setups (CI, scripted bootstraps), apply the equivalent SQL with explicit passwords; see the script as the canonical reference.

Then copy `template.env` (at the repo root) to `.env`:

    cp template.env .env

Edit `.env`:
* Replace `<%PASSWORD%>` in `GW_DATA_DB_URL` with the `gw_admin` password you just set.
* Replace `<%PORT%>` with the host port you mapped to 5432 (e.g. `5433`).

**Reset shortcut:** if your local DB ever gets into a weird state, you can wipe it and start over with:

    psql -d "postgresql://127.0.0.1:<PORT>/" -U postgres -f src/gw_data/db/scripts/_XX_drop_all.sql

### 3. Create and Seed your Database

With the database created, `gw_admin` ready, and `.env` filled in, you can create the tables and seed initial data.

    uv sync
    uv run alembic upgrade head

This should create 12 tables: `alembic_version`, `connectivity_edges`, `customers`, `g_nodes`, `installations`, `installers`, `messages`, `position_points`, `reading_channels`, `readings`, `user_installation_roles`, `users`.

Verify with `psql -d "postgresql://gw_admin:<PASSWORD>@127.0.0.1:<PORT>/gridworks" -c "\dt"`.

Then seed initial data:

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

The following queries are useful for analyzing TimescaleDB performance:

```
-- Display the size in MB of our two main tables
SELECT pg_size_pretty(hypertable_size('readings')) as "Readings Table Size", pg_size_pretty(hypertable_size('messages')) as "Messages Table Size";
```

```
-- Display the size of all database tables in order.
-- This will show each TimescaleDB chunk as a separate table.
SELECT
    table_schema || '.' || table_name AS table_full_name,
    pg_size_pretty(pg_total_relation_size('"' || table_schema || '"."' || table_name || '"')) AS size
FROM information_schema.tables
ORDER BY
    pg_total_relation_size('"' || table_schema || '"."' || table_name || '"') DESC;

```

```
-- Display compression stats for each chunk in the readings table
SELECT 
    chunk_name,
    pg_size_pretty(before_compression_total_bytes) AS size_before,
    pg_size_pretty(after_compression_total_bytes) AS size_after,
    100 - (after_compression_total_bytes::float / before_compression_total_bytes * 100) AS compression_ratio_pct
FROM chunk_compression_stats('readings');
```

```
-- Get the ID of the policy_compression job so you can manually run `CALL run_job` with it (e.g. after a bulk import).
SELECT job_id, proc_name, hypertable_name, config 
FROM timescaledb_information.jobs;
```
```
-- Get info (table, time range, etc.) about the TimescaleDB chunks.
SELECT * FROM timescaledb_information.chunks
```
