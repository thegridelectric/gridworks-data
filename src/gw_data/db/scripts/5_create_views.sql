-- DROP MATERIALIZED VIEW IF EXISTS gridworks.readings_1hour
CREATE MATERIALIZED VIEW gridworks.readings_1hour
WITH (timescaledb.continuous)
AS
SELECT 
	reading_channels.terminal_asset_alias AS terminal_asset_alias,
	reading_channels.name AS channel_name, 
	reading_channels.unit AS unit, 
	reading_channels.unit_type AS unit_type, 
	time_bucket(INTERVAL '1 hour', readings.timestamp) AS time_bucket, 
	time_weight('LOCF', readings.timestamp, readings.value) AS time_weight
FROM gridworks.readings 
JOIN gridworks.reading_channels ON reading_channels.id = readings.channel_id
GROUP BY time_bucket, reading_channels.terminal_asset_alias, reading_channels.name, reading_channels.unit, reading_channels.unit_type 
ORDER BY reading_channels.terminal_asset_alias, reading_channels.name, time_bucket;

-- DROP FUNCTION IF EXISTS gridworks.retrieve_readings_1s(timestamp with time zone, timestamp with time zone, text[]);
CREATE OR REPLACE FUNCTION gridworks.retrieve_readings_1s(
	t_start timestamp with time zone,
	t_end timestamp with time zone,
	channels text[])
    RETURNS TABLE(terminal_asset_alias text, channel_name text, unit text, unit_type text, time_bucket timestamp with time zone, value numeric) 
	LANGUAGE 'sql'

AS $BODY$
	
	SELECT 
		time_values.terminal_asset_alias,
		time_values.channel_name, 
		time_values.unit, 
		time_values.unit_type, 
		time_bucket_gapfill(INTERVAL '1 seconds', time_values.time_bucket) AS time_bucket_gapfilled, 
		locf(max(time_values.avg_value)) AS last_reading_value
	FROM (
		SELECT 
			rc.terminal_asset_alias,
			rc.name AS channel_name, 
			rc.unit, 
			rc.unit_type, 
			time_bucket(INTERVAL '1 seconds', r.timestamp) AS time_bucket, 
			avg(r.value) AS avg_value
			-- time_weight('LOCF', r.timestamp, r.value) AS time_weight
		FROM gridworks.readings r
		JOIN gridworks.reading_channels rc ON rc.id = r.channel_id
		WHERE 
			r.timestamp >= t_start --'2026-04-20T04:00:00Z'
			AND r.timestamp <= t_end --'2026-04-20T07:00:00Z'
			AND rc.name = ANY(channels)
		GROUP BY time_bucket, rc.name, rc.unit, rc.unit_type, rc.terminal_asset_alias
		ORDER BY rc.name, time_bucket
	) AS time_values
	WHERE 1=1
	AND time_values.time_bucket >= t_start
	AND time_values.time_bucket <= t_end
	GROUP BY time_values.terminal_asset_alias, time_values.channel_name, time_values.unit, time_values.unit_type, time_bucket_gapfilled
$BODY$;


-- Function to run the hourly calculations
select
	terminal_asset_alias,
	time_bucket(INTERVAL '1 hour', time_bucket_1s) AS time_bucket_1h,
	avg(hp_kw) as hp_kwh,
	avg(dist_kw) as dist_kwh,
	avg(store_change_kw) as store_change_kwh
from (
	select 
		*,
		500 * primary_flow_gpm * (hp_lwt_c - hp_ewt_c) * 9 / 5 / 3410 as hp_kw,
		500 * dist_flow_gpm * (dist_swt_c - store_flow_gpm) * 9 / 5 / 3410 as dist_kw,
		500 * (
			(1 - store_charge_discharge_0_1) * store_flow_gpm +
			store_charge_discharge_0_1 * primary_flow_gpm
		) * (store_charge_discharge_0_1 * 2 - 1) * (store_hot_pipe_c - store_cold_pipe_c) * 9 / 5 / 3410 as store_change_kw
	from (
		select
			terminal_asset_alias,
			time_bucket as time_bucket_1s,
			(AVG (value) FILTER (WHERE channel_name='primary-flow' AND unit='GpmTimes100') / 100) as primary_flow_gpm,
			(AVG (value) FILTER (WHERE channel_name='hp-lwt' AND unit='WaterTempCTimes1000') / 1000) as hp_lwt_c,
			(AVG (value) FILTER (WHERE channel_name='hp-ewt' AND unit='WaterTempCTimes1000') / 1000) as hp_ewt_c,
			(AVG (value) FILTER (WHERE channel_name='dist-flow' AND unit='GpmTimes100') / 100) as dist_flow_gpm,
			(AVG (value) FILTER (WHERE channel_name='dist-swt' AND unit='WaterTempCTimes1000') / 1000) as dist_swt_c,
			(AVG (value) FILTER (WHERE channel_name='dist-rwt' AND unit='WaterTempCTimes1000') / 1000) as dist_rwt_c,
			(AVG (value) FILTER (WHERE channel_name='store-flow' AND unit='GpmTimes100') / 100) as store_flow_gpm,
			(AVG (value) FILTER (WHERE channel_name='store-hot-pipe' AND unit='WaterTempCTimes1000') / 1000) as store_hot_pipe_c,
			(AVG (value) FILTER (WHERE channel_name='store-cold-pipe' AND unit='WaterTempCTimes1000') / 1000) as store_cold_pipe_c,
			(AVG (value) FILTER (WHERE channel_name='charge-discharge-relay3')) as store_charge_discharge_0_1
		from gridworks.fn_retrieve_readings_1s(
			t_start => TIMESTAMP '2026-04-20T03:00:00Z',
			t_end => TIMESTAMP '2026-04-20T10:00:00Z', 
			channels => ARRAY['hp-ewt','hp-lwt', 'primary-flow', 'dist-swt', 'dist-rwt', 'dist-flow', 'charge-discharge-relay3', 'store-hot-pipe', 'store-cold-pipe', 'store-flow']
		)
		group by terminal_asset_alias,time_bucket
	)
)
	
group by terminal_asset_alias,time_bucket_1h
order by terminal_asset_alias,time_bucket_1h
