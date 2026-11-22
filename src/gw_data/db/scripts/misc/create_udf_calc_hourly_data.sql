CREATE OR REPLACE FUNCTION gridworks.calc_hourly_data(
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
        lmp_usd_per_mwh float,
        ghi_w_m2 float,
        oat_source text,
        ws_source text
    )
    STABLE
	LANGUAGE 'sql'


AS $BODY$
    SELECT terminal_asset_alias, time_bucket,
    -- The heat pump's electricity is whichever of its units the house has;
    -- a house whose heat pump has no indoor unit (elm's Arctic) reads the
    -- outdoor unit alone. Empty only when neither unit reported.
    CASE WHEN hp_idu_w IS NULL AND hp_odu_w IS NULL THEN NULL
         ELSE (COALESCE(hp_idu_w, 0) + COALESCE(hp_odu_w, 0)) / 1000 END AS hp_kwh_el,
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
    -- Outdoor temperature and wind are the station's observation where it
    -- has one, the model gridpoint's where it does not, and the house's own
    -- forecast where neither exists. The source columns name the channel
    -- each hour's value was read from.
    COALESCE(kmlt_ws_mph, ommillinocket_ws_mph, forecast_ws_mph) AS ws_mph,
    COALESCE(kmlt_oat_f, ommillinocket_oat_f, forecast_oat_f) AS oat_f,
    total_usd_per_mwh,
    buffer_available_kwh,
    lmp_usd_per_mwh,
    ghi_w_m2,
    CASE WHEN kmlt_oat_f IS NOT NULL THEN 'kmlt-temperature'
         WHEN ommillinocket_oat_f IS NOT NULL THEN 'ommillinocket-temperature'
         WHEN forecast_oat_f IS NOT NULL THEN 'forecast-oat' END AS oat_source,
    CASE WHEN kmlt_ws_mph IS NOT NULL THEN 'kmlt-windspeed'
         WHEN ommillinocket_ws_mph IS NOT NULL THEN 'ommillinocket-windspeed'
         WHEN forecast_ws_mph IS NOT NULL THEN 'forecast-ws' END AS ws_source
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
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'W')) FILTER (WHERE channel_name='hp-idu-pwr' AND quantity='Power') AS hp_idu_w,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'W')) FILTER (WHERE channel_name='hp-odu-pwr' AND quantity='Power') AS hp_odu_w,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'F')) FILTER (WHERE channel_name='hp-lwt' AND quantity='Temperature') AS hp_avg_lwt,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'F')) FILTER (WHERE channel_name='hp-ewt' AND quantity='Temperature') AS hp_avg_ewt,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'F')) FILTER (WHERE channel_name='dist-swt' AND quantity='Temperature') AS dist_avg_swt,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'F')) FILTER (WHERE channel_name='dist-rwt' AND quantity='Temperature') AS dist_avg_rwt,
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
                    quantity,
                    scale,
                    base_unit,
                    time_bucket,
                    interpolated_average(
                        time_weight,
                        time_bucket,
                        '1 hour',
                        LAG(time_weight) OVER (PARTITION BY terminal_asset_alias,channel_name,unit_type,unit ORDER BY time_bucket),
                        LEAD(time_weight) OVER (PARTITION BY terminal_asset_alias,channel_name,unit_type,unit ORDER BY time_bucket)
                    ) AS avg_value
                FROM (
                    -- A reading is selected by channel name and quantity; its unit_scale
                    -- row says what the stored integer is, so a channel recorded in either
                    -- unit enum, in any era, reads as the same quantity.
                    SELECT v.*, us.quantity, us.scale, us.base_unit
                    FROM gridworks.readings_1hr v
                    LEFT JOIN gridworks.unit_scale us ON us.unit_type = v.unit_type AND us.unit = v.unit
                    WHERE 1=1
                    AND v.time_bucket >= t_start
                    AND v.time_bucket <= t_end
                )
            )
            GROUP BY time_bucket,terminal_asset_alias
            ORDER BY time_bucket
        ) AS avg_values ON kwh_values.time_bucket = avg_value_time_bucket AND kwh_values.terminal_asset_alias = avg_value_ta
        JOIN (
            SELECT
                terminal_asset_alias AS first_value_ta,
                time_bucket AS first_value_time_bucket,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='buffer-depth1' AND quantity='Temperature') AS buffer_depth1_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='buffer-depth2' AND quantity='Temperature') AS buffer_depth2_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='buffer-depth3' AND quantity='Temperature') AS buffer_depth3_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='buffer-depth4' AND quantity='Temperature') AS buffer_depth4_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank1-depth1' AND quantity='Temperature') AS tank1_depth1_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank1-depth2' AND quantity='Temperature') AS tank1_depth2_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank1-depth3' AND quantity='Temperature') AS tank1_depth3_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank1-depth4' AND quantity='Temperature') AS tank1_depth4_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank2-depth1' AND quantity='Temperature') AS tank2_depth1_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank2-depth2' AND quantity='Temperature') AS tank2_depth2_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank2-depth3' AND quantity='Temperature') AS tank2_depth3_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank2-depth4' AND quantity='Temperature') AS tank2_depth4_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank3-depth1' AND quantity='Temperature') AS tank3_depth1_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank3-depth2' AND quantity='Temperature') AS tank3_depth2_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank3-depth3' AND quantity='Temperature') AS tank3_depth3_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='tank3-depth4' AND quantity='Temperature') AS tank3_depth4_start,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'F')) FILTER (WHERE channel_name='forecast-oat' AND quantity='Temperature') AS forecast_oat_f,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'mph')) FILTER (WHERE channel_name='forecast-ws' AND quantity='WindSpeed') AS forecast_ws_mph,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'USD')) FILTER (WHERE channel_name='total-usd-per-mwh' AND quantity='Currency') AS total_usd_per_mwh,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'USD')) FILTER (WHERE channel_name='lmp-usd-per-mwh' AND quantity='Currency') AS lmp_usd_per_mwh,
                AVG (gridworks.in_unit(first_val, scale, base_unit, 'kWh')) FILTER (WHERE channel_name='buffer-available-kwh' AND quantity='Energy') AS buffer_available_kwh
                
            FROM (
                SELECT 
                    terminal_asset_alias,
                    channel_name,
                    quantity,
                    scale,
                    base_unit,
                    time_bucket,
                    first_val(time_weight) AS first_val
                FROM (
                    SELECT v.*, us.quantity, us.scale, us.base_unit
                    FROM gridworks.readings_1hr v
                    LEFT JOIN gridworks.unit_scale us ON us.unit_type = v.unit_type AND us.unit = v.unit
                    WHERE 1=1
                    AND v.time_bucket >= t_start
                    AND v.time_bucket <= t_end
                    ORDER BY v.time_bucket
                )
            )
            GROUP BY time_bucket,terminal_asset_alias
            ORDER BY time_bucket
        ) AS first_values ON kwh_values.time_bucket = first_value_time_bucket AND kwh_values.terminal_asset_alias = first_value_ta
        LEFT JOIN (
            -- The weather GNode's observed channels, read once per hour and
            -- joined to every house. The GNode alias and the channel names are
            -- constants here: no word yet states which station a house's hourly
            -- weather is read from (the missing word is a house-to-station
            -- binding; gw.weather.channel.gt names the station, not the house).
            SELECT
                time_bucket AS weather_time_bucket,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'F')) FILTER (WHERE channel_name='kmlt-temperature' AND quantity='Temperature') AS kmlt_oat_f,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'mph')) FILTER (WHERE channel_name='kmlt-windspeed' AND quantity='WindSpeed') AS kmlt_ws_mph,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'F')) FILTER (WHERE channel_name='ommillinocket-temperature' AND quantity='Temperature') AS ommillinocket_oat_f,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'mph')) FILTER (WHERE channel_name='ommillinocket-windspeed' AND quantity='WindSpeed') AS ommillinocket_ws_mph,
                AVG (gridworks.in_unit(avg_value, scale, base_unit, 'W/m2')) FILTER (WHERE channel_name='ommillinocket-irradiance' AND quantity='Irradiance') AS ghi_w_m2
            FROM (
                SELECT
                    channel_name,
                    quantity,
                    scale,
                    base_unit,
                    time_bucket,
                    interpolated_average(
                        time_weight,
                        time_bucket,
                        '1 hour',
                        LAG(time_weight) OVER (PARTITION BY channel_name,unit_type,unit ORDER BY time_bucket),
                        LEAD(time_weight) OVER (PARTITION BY channel_name,unit_type,unit ORDER BY time_bucket)
                    ) AS avg_value
                FROM (
                    SELECT v.*, us.quantity, us.scale, us.base_unit
                    FROM gridworks.readings_1hr v
                    LEFT JOIN gridworks.unit_scale us ON us.unit_type = v.unit_type AND us.unit = v.unit
                    WHERE v.terminal_asset_alias = 'hw1.isone.weather'
                    AND v.time_bucket >= t_start
                    AND v.time_bucket <= t_end
                )
            )
            GROUP BY time_bucket
        ) AS weather ON kwh_values.time_bucket = weather_time_bucket
        OFFSET 0 -- Optimization 
    )
    ORDER BY time_bucket
$BODY$;
