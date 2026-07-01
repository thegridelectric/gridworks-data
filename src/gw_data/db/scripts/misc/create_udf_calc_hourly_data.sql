CREATE FUNCTION gridworks.calc_hourly_data(
	t_start timestamp with time zone,
	t_end timestamp with time zone)
    RETURNS TABLE(
        -- NOTE that this table must match the cached_hourly_data table!
        terminal_asset_alias text,
        time_bucket timestamp with time zone,
        hp_kwh_el float,
        hp_kwh_th float,
        dist_kwh float,
        store_change_kwh float,
        hp_avg_lwt float,
        hp_avg_ewt float,
        dist_avg_swt float,
        dist_avg_rwt float,
        buffer_depth1_start float,
        buffer_depth2_start float,
        buffer_depth3_start float,
        buffer_depth4_start float,
        tank1_depth1_start float,
        tank1_depth2_start float,
        tank1_depth3_start float,
        tank1_depth4_start float,
        tank2_depth1_start float,
        tank2_depth2_start float,
        tank2_depth3_start float,
        tank2_depth4_start float,
        tank3_depth1_start float,
        tank3_depth2_start float,
        tank3_depth3_start float,
        tank3_depth4_start float,
        relay_3_pulled_fraction float,
        relay_5_pulled_fraction float,
        relay_6_pulled_fraction float,
        relay_9_pulled_fraction float,
        zone1_heatcall_fraction float,
        zone2_heatcall_fraction float,
        zone3_heatcall_fraction float,
        zone4_heatcall_fraction float,
        ws_mph float,
        oat_f float,
        total_usd_per_mwh float,
        buffer_available_kwh float,
        lmp_usd_per_mwh float
    )
    STABLE
	LANGUAGE 'sql'


AS $BODY$
    SELECT terminal_asset_alias, time_bucket,
    (hp_idu_w + hp_odu_w) / 1000 AS hp_kwh_el,
    hp_kwh AS hp_kwh_th,
    dist_kwh,
    store_change_kwh,
    hp_avg_lwt,hp_avg_ewt,
    dist_avg_swt, dist_avg_rwt,
    buffer_depth1_start, buffer_depth2_start, buffer_depth3_start, buffer_depth4_start,
    tank1_depth1_start, tank1_depth2_start, tank1_depth3_start, tank1_depth4_start,
    tank2_depth1_start, tank2_depth2_start, tank2_depth3_start, tank2_depth4_start,
    tank3_depth1_start, tank3_depth2_start, tank3_depth3_start, tank3_depth4_start,
    relay_3_pulled_fraction, relay_5_pulled_fraction, relay_6_pulled_fraction, relay_9_pulled_fraction,
    zone1_heatcall_fraction, zone2_heatcall_fraction, zone3_heatcall_fraction, zone4_heatcall_fraction,
    ws_mph, oat_f,
    total_usd_per_mwh,
    buffer_available_kwh,
    lmp_usd_per_mwh
    FROM
    (
        SELECT * FROM (
            SELECT terminal_asset_alias, time_bucket, hp_kwh, dist_kwh, store_change_kwh
            FROM gridworks.calc_energy_1hr(t_start => t_start, t_end => t_end)
        ) AS kwh_values
        JOIN (
            SELECT
                terminal_asset_alias AS avg_value_ta,
                time_bucket AS avg_value_time_bucket,
                AVG (avg_value) FILTER (WHERE channel_name='hp-idu-pwr' AND unit='PowerW') AS hp_idu_w,
                AVG (avg_value) FILTER (WHERE channel_name='hp-odu-pwr' AND unit='PowerW') AS hp_odu_w,
                gridworks.C2F(AVG (avg_value) FILTER (WHERE channel_name='hp-lwt' AND unit='WaterTempCTimes1000') / 1000) AS hp_avg_lwt,
                gridworks.C2F(AVG (avg_value) FILTER (WHERE channel_name='hp-ewt' AND unit='WaterTempCTimes1000') / 1000) AS hp_avg_ewt,
                gridworks.C2F(AVG (avg_value) FILTER (WHERE channel_name='dist-swt' AND unit='WaterTempCTimes1000') / 1000) AS dist_avg_swt,
                gridworks.C2F(AVG (avg_value) FILTER (WHERE channel_name='dist-rwt' AND unit='WaterTempCTimes1000') / 1000) AS dist_avg_rwt,
                AVG (avg_value) FILTER (where channel_name like '%-relay3') AS relay_3_pulled_fraction,
                AVG (avg_value) FILTER (where channel_name like '%-relay5') AS relay_5_pulled_fraction,
                AVG (avg_value) FILTER (where channel_name like '%-relay6') AS relay_6_pulled_fraction,
                AVG (avg_value) FILTER (where channel_name like '%-relay9') AS relay_9_pulled_fraction,
                AVG (avg_value) FILTER (where channel_name like 'zone1-%-heat-call') AS zone1_heatcall_fraction,
                AVG (avg_value) FILTER (where channel_name like 'zone2-%-heat-call') AS zone2_heatcall_fraction,
                AVG (avg_value) FILTER (where channel_name like 'zone3-%-heat-call') AS zone3_heatcall_fraction,
                AVG (avg_value) FILTER (where channel_name like 'zone4-%-heat-call') AS zone4_heatcall_fraction
            FROM (
                SELECT 
                    terminal_asset_alias,
                    channel_name,
                    unit,
                    time_bucket,
                    interpolated_average(
                        time_weight,
                        time_bucket,
                        '1 hour',
                        LAG(time_weight) OVER (PARTITION BY terminal_asset_alias,channel_name,unit ORDER BY time_bucket),
                        LEAD(time_weight) OVER (PARTITION BY terminal_asset_alias,channel_name,unit ORDER BY time_bucket)
                    ) AS avg_value
                FROM (
                    SELECT * FROM gridworks.readings_1hr
                    WHERE 1=1
                    AND time_bucket >= t_start
                    AND time_bucket <= t_end
                )
            )
            GROUP BY time_bucket,terminal_asset_alias
            ORDER BY time_bucket
        ) AS avg_values ON kwh_values.time_bucket = avg_value_time_bucket AND kwh_values.terminal_asset_alias = avg_value_ta
        JOIN (
            SELECT
                terminal_asset_alias AS first_value_ta,
                time_bucket AS first_value_time_bucket,
                AVG (first_val) FILTER (WHERE channel_name='buffer-depth1' AND unit='FahrenheitX100') / 100 AS buffer_depth1_start,
                AVG (first_val) FILTER (WHERE channel_name='buffer-depth2' AND unit='FahrenheitX100') / 100 AS buffer_depth2_start,
                AVG (first_val) FILTER (WHERE channel_name='buffer-depth3' AND unit='FahrenheitX100') / 100 AS buffer_depth3_start,
                AVG (first_val) FILTER (WHERE channel_name='buffer-depth4' AND unit='FahrenheitX100') / 100 AS buffer_depth4_start,
                AVG (first_val) FILTER (WHERE channel_name='tank1-depth1' AND unit='FahrenheitX100') / 100 AS tank1_depth1_start,
                AVG (first_val) FILTER (WHERE channel_name='tank1-depth2' AND unit='FahrenheitX100') / 100 AS tank1_depth2_start,
                AVG (first_val) FILTER (WHERE channel_name='tank1-depth3' AND unit='FahrenheitX100') / 100 AS tank1_depth3_start,
                AVG (first_val) FILTER (WHERE channel_name='tank1-depth4' AND unit='FahrenheitX100') / 100 AS tank1_depth4_start,
                AVG (first_val) FILTER (WHERE channel_name='tank2-depth1' AND unit='FahrenheitX100') / 100 AS tank2_depth1_start,
                AVG (first_val) FILTER (WHERE channel_name='tank2-depth2' AND unit='FahrenheitX100') / 100 AS tank2_depth2_start,
                AVG (first_val) FILTER (WHERE channel_name='tank2-depth3' AND unit='FahrenheitX100') / 100 AS tank2_depth3_start,
                AVG (first_val) FILTER (WHERE channel_name='tank2-depth4' AND unit='FahrenheitX100') / 100 AS tank2_depth4_start,
                AVG (first_val) FILTER (WHERE channel_name='tank3-depth1' AND unit='FahrenheitX100') / 100 AS tank3_depth1_start,
                AVG (first_val) FILTER (WHERE channel_name='tank3-depth2' AND unit='FahrenheitX100') / 100 AS tank3_depth2_start,
                AVG (first_val) FILTER (WHERE channel_name='tank3-depth3' AND unit='FahrenheitX100') / 100 AS tank3_depth3_start,
                AVG (first_val) FILTER (WHERE channel_name='tank3-depth4' AND unit='FahrenheitX100') / 100 AS tank3_depth4_start,
                AVG (first_val) FILTER (where channel_name = 'forecast-oat' AND unit='FahrenheitX100') / 100 AS oat_f,
                AVG (first_val) FILTER (where channel_name = 'forecast-ws' AND unit='MilesPerHourX1000') / 1000 AS ws_mph,
                AVG (first_val) FILTER (where channel_name = 'total-usd-per-mwh' AND unit='DollarsX1000') / 1000 AS total_usd_per_mwh,
                AVG (first_val) FILTER (where channel_name = 'lmp-usd-per-mwh' AND unit='DollarsX1000') / 1000 AS lmp_usd_per_mwh,
                AVG (first_val) FILTER (where channel_name = 'buffer-available-kwh' AND unit='KilowattHoursX1000') / 1000 AS buffer_available_kwh			
                
            FROM (
                SELECT 
                    terminal_asset_alias,
                    channel_name,
                    unit,
                    time_bucket,
                    first_val(time_weight) AS first_val
                FROM (
                    SELECT * FROM gridworks.readings_1hr
                    WHERE 1=1
                    AND time_bucket >= t_start
                    AND time_bucket <= t_end
                    ORDER BY time_bucket
                )
            )
            GROUP BY time_bucket,terminal_asset_alias
            ORDER BY time_bucket
        ) AS first_values ON kwh_values.time_bucket = first_value_time_bucket AND kwh_values.terminal_asset_alias = first_value_ta
        OFFSET 0 -- Optimization 
    )
    ORDER BY time_bucket
$BODY$;
