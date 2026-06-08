--DROP DATABASE gridworks WITH (FORCE);

-- This line may have to be done by gw_admin
DROP SCHEMA gridworks;

REVOKE CONNECT ON DATABASE tsdb FROM gw_visualizer;
DROP USER gw_visualizer;

REVOKE CONNECT ON DATABASE tsdb FROM gw_journalkeeper;
DROP USER gw_journalkeeper;

REVOKE ALL ON DATABASE tsdb FROM gw_admin;
DROP USER gw_admin;
