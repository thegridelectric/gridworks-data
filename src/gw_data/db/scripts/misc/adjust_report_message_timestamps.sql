-- report.event message parsing had a bug that caused the timestamps to get set in local time rather than UTC.
-- This script fixes them.
-- (Unfortunately we can't just UPDATE a timestamp column with TimescaleDB)
-- This never needed to be run in prod, since the server local time was UTC.

-- SET temp_buffers = '2000MB'; 

BEGIN;

CREATE TEMP TABLE temp_report_messages AS
SELECT 
	id, 
	"timestamp" + INTERVAL '6 hours' AS "timestamp",
	from_alias, 
	created_at + INTERVAL '6 hours' AS created_at,
	persisted_at, 
	message_type_name, 
	payload
FROM gridworks.messages 
-- where id='85c153a2-ebf6-4a24-83ba-5dba12967d87';
WHERE message_type_name='report.event';

DELETE FROM gridworks.messages
-- where id='85c153a2-ebf6-4a24-83ba-5dba12967d87';
WHERE message_type_name='report.event';

INSERT INTO gridworks.messages SELECT * FROM temp_report_messages;

WITH 
	q1 AS (
	    SELECT COUNT(*) as cnt, ROW_NUMBER() OVER () AS rn FROM gridworks.messages
	),
	q2 AS (
	    SELECT *, ROW_NUMBER() OVER () AS rn 
		FROM gridworks.messages 
		where id='85c153a2-ebf6-4a24-83ba-5dba12967d87'
	)
SELECT 
    q1.cnt, 
    q2.*
FROM q1
FULL OUTER JOIN q2 ON q1.rn = q2.rn;

-- Fix the OAT and WS readings
select id from gridworks.reading_channels where name = 'forecast-ws';
update gridworks.readings
set value=value * 10
where channel_id in (
	'792a01bc-1b95-4434-97e5-30d64c000024',
	'3310111e-33ab-4c07-bab1-7d4c7d464201',
	'60bb6806-e5a5-4a06-a60e-c26b0bf77e59',
	'a349f893-61a7-4c65-8e33-998517d06fb0',
	'f0ae219e-73d1-4c61-9c02-a13e940b8737',
	'97a42794-bb6b-4a4d-be6f-1c5c9f955af7'
)


COMMIT
-- ROLLBACK;