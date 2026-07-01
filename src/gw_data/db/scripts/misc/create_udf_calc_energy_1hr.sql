CREATE FUNCTION gridworks.calc_energy_1hr(
	t_start timestamp with time zone,
	t_end timestamp with time zone)
    RETURNS TABLE(
        terminal_asset_alias text,
        time_bucket timestamp with time zone,
        hp_kwh float,
        dist_kwh float,
        store_change_kwh float
    ) 
    STABLE
	LANGUAGE 'sql'

AS $BODY$

    SELECT
        terminal_asset_alias,
        time_bucket(INTERVAL '1 hour', time_bucket_1s) AS time_bucket_1h,
        avg(hp_kw) AS hp_kwh,
        avg(dist_kw) AS dist_kwh,
        avg(store_change_kw) AS store_change_kwh
    FROM (
        SELECT 
            *,
            500 * primary_flow_gpm * (hp_lwt_c - hp_ewt_c) * 9 / 5 / 3410 AS hp_kw,
            500 * dist_flow_gpm * (dist_swt_c - dist_rwt_c) * 9 / 5 / 3410 AS dist_kw,
            500 * (
                (1 - store_charge_discharge_0_1) * store_flow_gpm +
                store_charge_discharge_0_1 * primary_flow_gpm
            ) * (store_charge_discharge_0_1 * 2 - 1) * (store_hot_pipe_c - store_cold_pipe_c) * 9 / 5 / 3410 AS store_change_kw
        FROM (
            SELECT
                terminal_asset_alias,
                time_bucket AS time_bucket_1s,
                (AVG (value) FILTER (WHERE channel_name='primary-flow' AND unit='GpmTimes100') / 100) AS primary_flow_gpm,
                (AVG (value) FILTER (WHERE channel_name='hp-lwt' AND unit='WaterTempCTimes1000') / 1000) AS hp_lwt_c,
                (AVG (value) FILTER (WHERE channel_name='hp-ewt' AND unit='WaterTempCTimes1000') / 1000) AS hp_ewt_c,
                (AVG (value) FILTER (WHERE channel_name='dist-flow' AND unit='GpmTimes100') / 100) AS dist_flow_gpm,
                (AVG (value) FILTER (WHERE channel_name='dist-swt' AND unit='WaterTempCTimes1000') / 1000) AS dist_swt_c,
                (AVG (value) FILTER (WHERE channel_name='dist-rwt' AND unit='WaterTempCTimes1000') / 1000) AS dist_rwt_c,
                (AVG (value) FILTER (WHERE channel_name='store-flow' AND unit='GpmTimes100') / 100) AS store_flow_gpm,
                (AVG (value) FILTER (WHERE channel_name='store-hot-pipe' AND unit='WaterTempCTimes1000') / 1000) AS store_hot_pipe_c,
                (AVG (value) FILTER (WHERE channel_name='store-cold-pipe' AND unit='WaterTempCTimes1000') / 1000) AS store_cold_pipe_c,
                (AVG (value) FILTER (WHERE channel_name='charge-discharge-relay3')) AS store_charge_discharge_0_1
            FROM gridworks.retrieve_readings_1s(
                t_start => t_start,
                t_end => t_end, 
                channels => ARRAY['hp-ewt','hp-lwt', 'primary-flow', 'dist-swt', 'dist-rwt', 'dist-flow', 'charge-discharge-relay3', 'store-hot-pipe', 'store-cold-pipe', 'store-flow']
            )
            GROUP BY terminal_asset_alias,time_bucket
        )
    )
        
    GROUP BY terminal_asset_alias,time_bucket_1h
    ORDER BY terminal_asset_alias,time_bucket_1h
$BODY$;
