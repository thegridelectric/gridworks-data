-- Find readings for specific channels, installations, timeframe
select rc.terminal_asset_alias,rc.name,r.timestamp,r.value
from gridworks.readings r
join gridworks.reading_channels rc on r.channel_id = rc.id
where 1=1
	and (rc.name like '%whitewire%'	or rc.name like '%heat-call%')
	and rc.terminal_asset_alias like '%beech%'
	and timestamp >= '2026-04-20T04:00:00Z'
	and timestamp <= '2026-04-20T05:00:00Z'
order by r.timestamp,rc.terminal_asset_alias
limit 100;

-- Find channels for an installation
select * from gridworks.reading_channels
where terminal_asset_alias like '%beech%'
order by name,terminal_asset_alias;

-- Find messages for an installation & timeframe
select * from gridworks.messages
where 1=1
and from_alias like '%beech%'
and timestamp >= '2026-04-20T04:00:00Z'
and timestamp <= '2026-04-20T05:00:00Z'
limit 100;

-- Total database size
SELECT pg_size_pretty(pg_database_size('tsdb')) AS size;

-- Display the size of all database tables in order.
-- This will show each TimescaleDB chunk as a separate table.
SELECT
    table_schema || '.' || table_name AS table_full_name,
    pg_size_pretty(pg_total_relation_size('"' || table_schema || '"."' || table_name || '"')) AS size
FROM information_schema.tables
ORDER BY
    pg_total_relation_size('"' || table_schema || '"."' || table_name || '"') DESC;

-- Display compression stats for each chunk in the readings table
SELECT 
    chunk_name,
    pg_size_pretty(before_compression_total_bytes) AS size_before,
    pg_size_pretty(after_compression_total_bytes) AS size_after,
    100 - (after_compression_total_bytes::float / before_compression_total_bytes * 100) AS compression_ratio_pct
FROM chunk_compression_stats('gridworks.readings');

-- Get info (table, time range, etc.) about the TimescaleDB chunks.
SELECT * FROM timescaledb_information.chunks

-- Display the size in MB of our two main tables across all its chunks
SELECT 
	pg_size_pretty(hypertable_size('gridworks.readings')) as "Readings Table Size", 
	pg_size_pretty(hypertable_size('gridworks.messages')) as "Messages Table Size";

-- Detailed size for a full hypertable across all its chunks
SELECT
    pg_size_pretty(table_bytes) AS data_size,
    pg_size_pretty(index_bytes) AS index_size,
    pg_size_pretty(toast_bytes) AS toast_size,
    pg_size_pretty(total_bytes) AS total_size
FROM hypertable_detailed_size('gridworks.readings');

-- Info about timescaledb jobs
select * from timescaledb_information.jobs;

-- Manually run a job (e.g. run compression after an import).
-- Fill in job_id based on the query above
CALL run_job(job_id);



