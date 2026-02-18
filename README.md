# Gridworks Data

This project contains code related to working with databases in the GridWorks ecosystem.

Our platform is PostgreSQL, with the TimescaleDB (+toolkit) extensions for efficiently handling time-series data.

## Database Setup

The following steps will get you set up to run with the database.

### 1. Install the Docker image with PostgreSQL and TimescaleDB.

Make sure you have Docker installed.
(If you have previously set up the RabbitMQ server from `gridworks-base` then you should already have it.)

Detailed instructions for setting up the TimescaleDB docker image are online at: 
https://www.tigerdata.com/docs/self-hosted/latest/install/installation-docker

A few things to note:
* Install the `timescaledb-ha:pg18-ts2.25` Docker image for PostgreSQL v18 and TimescaleDB v2.25. (The `ha` part of the name is important! Without it you will get the "lite" version of TimescaleDB which does not have all our required functionality.)
* When building the container, you need to include a port mapping for 5432. If you are not already running a PostgreSQL instance on your machine than you can just map `5432:5432`. But if you are already running PostgreSQL (either with Docker or natively) you will need to select a different port (e.g. `5433:5432`).
* When building the container, you need to include a `POSTGRES_PASSWORD` env variable, which will be the password for the default `postgres` user.

### 2. Create the Database

For this step you will need the `psql` PostgreSQL command-line client, of a version at least as high as the PostgreSQL server.
You can do this via your usual package manager (e.g. `sudo apt install psql`).
You can check your installed version via `psql --version`.

(You may also want to install the `pgAdmin` tool as a GUI for conveniently inspecting the database and running SQL queries.)

Once you have `psql` installed, you can use it to run the initialization script as follows (replace `%PORT%` with the port number you mapped to 5432 when you built your Docker container in Step 1):

    psql -d postgresql://127.0.01:<%PORT%>/ -U postgres -f src/gw_data/db/scripts/0_server_init.sql

This will prompt you first for the `postgres` user password.
Enter the password you specified as the `POSTGRES_PASSWORD` env variable when you built your Docker container.

This will also prompt you to create a password for the `gw_admin` database user.
This user is what we will use for all our database admin operations from this point forward.
(The built-in `postgres` user is like the `root` OS user -- we don't want to use it unless we have to.)

Copy your `template.env` file to `.env` (`cp template.env .env`).
In the `GW_DATA_DB_URL` value, replace `<%PASSWORD%>` with the `gw_admin` password you just set.
Also, replace `<%PORT%>` with the mapped port number.

NOTE -- if things ever go badly and you want to restart your database from scratch, there is another script for that:

    psql -d postgresql://127.0.01:<%PORT%>/ -U postgres -f src/gw_data/db/scripts/_XX_drop_all.sql

## 3. Create and Seed your Database

Once your database is created, the `gw_admin` user is created, and the `.env` file is set up accordingly, you can create our tables and seed them with data.

First, `uv sync` to download the project dependencies.

We use `alembic` to manage changes to our schema.
Upgrade to the most recent schema with the following command:

    uv run alembic upgrade head

This should create many tables in the database (e.g. `g_nodes` and `messages`).
Use psql or pgAdmin to confirm that this worked.

Next, run the seed script to populate some initial data from the database with the following command:

    uv run python ./src/gw_data/db/scripts/1_db_seed.py

In the future we will have a more comprehensive seeding process that will ingest some actual message data.


## Best Practices for Databases

The following are some best practices that we should follow when at all possible:

* Primary Keys should be UUIDs, stored as the DB-native UUID type
* Dates/Times should be stored as `TIMESTAMPTZ`
* Migrations should be encouraged and done frequently to provide new functionality. Database schema is always temporary.
* Each application that uses that database should have its own dedicated user, with the minimal set of permissions. (In particular, `postgres` should never be used at all, and `gw_admin` should only be used for migrations and other tasks that require database ownership.)
