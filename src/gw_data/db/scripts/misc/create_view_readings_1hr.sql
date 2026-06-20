CREATE MATERIALIZED VIEW gridworks.readings_1hr
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
	ORDER BY reading_channels.terminal_asset_alias, reading_channels.name, time_bucket
WITH NO DATA;