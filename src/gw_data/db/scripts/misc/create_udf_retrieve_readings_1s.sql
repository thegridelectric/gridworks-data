-- One row per channel per second over the window. A channel's
-- reading_channels rows across layout eras are one lineage, so a second's
-- value is the lineage's latest reading and the unit beside it is that
-- reading's: a retired row's last value stops where the next row's first
-- reading starts. Casts sit inside the inner select because locf must be
-- the top-level call of its output column.
CREATE OR REPLACE FUNCTION gridworks.retrieve_readings_1s(
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
		locf(max(time_values.unit)) AS unit,
		locf(max(time_values.unit_type)) AS unit_type,
		time_bucket_gapfill(INTERVAL '1 seconds', time_values.time_bucket) AS time_bucket_gapfilled,
		locf(max(time_values.last_value)) AS last_reading_value
	FROM (
		SELECT
			rc.terminal_asset_alias::text,
			rc.name::text AS channel_name,
			last(rc.unit, r.timestamp)::text AS unit,
			last(rc.unit_type, r.timestamp)::text AS unit_type,
			time_bucket(INTERVAL '1 seconds', r.timestamp) AS time_bucket,
			last(r.value, r.timestamp)::numeric AS last_value
		FROM gridworks.readings r
		JOIN gridworks.reading_channels rc ON rc.id = r.channel_id
		WHERE
			r.timestamp >= t_start
			AND r.timestamp <= t_end
			AND rc.name = ANY(channels)
		GROUP BY time_bucket, rc.name, rc.terminal_asset_alias
	) AS time_values
	WHERE time_values.time_bucket >= t_start
	AND time_values.time_bucket <= t_end
	GROUP BY time_values.terminal_asset_alias, time_values.channel_name, time_bucket_gapfilled
$BODY$;
