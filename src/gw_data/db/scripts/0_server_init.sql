CREATE DATABASE gridworks;

CREATE USER gw_admin;
GRANT ALL ON DATABASE gridworks TO gw_admin; 
ALTER DATABASE gridworks OWNER TO gw_admin;
\password gw_admin
