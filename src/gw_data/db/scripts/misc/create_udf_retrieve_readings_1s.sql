CREATE FUNCTION gridworks.retrieve_readings_1s(
	t_start timestamp with time zone,
	t_end timestamp with time zone,
	channels text[])
    RETURNS TABLE(terminal_asset_alias text, channel_name text, unit text, unit_type text, time_bucket timestamp with time zone, value numeric) 
    STABLE
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