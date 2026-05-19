DROP DATABASE gridworks WITH (FORCE);
DROP USER gw_admin;
--REASSIGN OWNED BY gw_writer TO postgres;
DROP USER gw_writer;
DROP USER gw_reader;