CREATE VIEW readings_pretty AS
SELECT
    dc.name AS name,
    r.value AS value,
    dc.telemetry_name AS telemetry_name,
    timestamp AS time,
    r.message_id AS message_id
FROM
    readings r
JOIN
    data_channels dc
ON
    r.data_channel_id = dc.id;



SELECT * FROM preadings WHERE name LIKE '%buffer%' LIMIT 5;


CREATE OR REPLACE VIEW msg_pretty AS
SELECT
    payload, from_alias, message_type_name, persisted_at AS message_persisted, created_at AS message_created
FROM messages;




SELECT COUNT(*) from messages;

SELECT COUNT(*) FROM messages WHERE message_type_name = 'power.watts';

SELECT from_alias, message_type_name, message_created FROM msg_pretty WHERE message_type_name LIKE '%status%' LIMIT 5;

SELECT pg_size_pretty(pg_database_size('gridworks')) AS size;
SELECT * FROM msg_pretty WHERE message_type_name LIKE '%param%';

SELECT id, from_alias, message_type_name, persisted_at FROM messages WHERE message_type_name LIKE '%param%';

DELETE FROM messages WHERE id = 'bf06df07-36a5-4e54-ae64-37dea6041ea8';

SELECT MIN(time) AS earliest, MAX(time) AS latest FROM  readings_pretty;
SELECT MIN(message_created) AS earliest, MAX(message_created) AS latest FROM  msg_pretty;

SELECT from_alias, message_type_name, message_created FROM msg_pretty WHERE message_type_name LIKE '%batched%' LIMIT 5;
