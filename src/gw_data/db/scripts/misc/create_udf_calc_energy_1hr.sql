CREATE OR REPLACE FUNCTION gridworks.calc_energy_1hr(
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
            -- A reading is selected by channel name and quantity; its unit_scale
            -- row says what the stored integer is, so a channel recorded in either
            -- unit enum, in any era, reads as the same quantity.
            SELECT
                r.terminal_asset_alias,
                r.time_bucket AS time_bucket_1s,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'gpm')) FILTER (WHERE r.channel_name='primary-flow' AND us.quantity='FlowRate') AS primary_flow_gpm,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'C')) FILTER (WHERE r.channel_name='hp-lwt' AND us.quantity='Temperature') AS hp_lwt_c,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'C')) FILTER (WHERE r.channel_name='hp-ewt' AND us.quantity='Temperature') AS hp_ewt_c,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'gpm')) FILTER (WHERE r.channel_name='dist-flow' AND us.quantity='FlowRate') AS dist_flow_gpm,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'C')) FILTER (WHERE r.channel_name='dist-swt' AND us.quantity='Temperature') AS dist_swt_c,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'C')) FILTER (WHERE r.channel_name='dist-rwt' AND us.quantity='Temperature') AS dist_rwt_c,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'gpm')) FILTER (WHERE r.channel_name='store-flow' AND us.quantity='FlowRate') AS store_flow_gpm,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'C')) FILTER (WHERE r.channel_name='store-hot-pipe' AND us.quantity='Temperature') AS store_hot_pipe_c,
                AVG (gridworks.in_unit(r.value, us.scale, us.base_unit, 'C')) FILTER (WHERE r.channel_name='store-cold-pipe' AND us.quantity='Temperature') AS store_cold_pipe_c,
                AVG (r.value) FILTER (WHERE r.channel_name='charge-discharge-relay3') AS store_charge_discharge_0_1
            FROM gridworks.retrieve_readings_1s(
                t_start => t_start,
                t_end => t_end, 
                channels => ARRAY['hp-ewt','hp-lwt', 'primary-flow', 'dist-swt', 'dist-rwt', 'dist-flow', 'charge-discharge-relay3', 'store-hot-pipe', 'store-cold-pipe', 'store-flow']
            ) AS r
            LEFT JOIN gridworks.unit_scale us ON us.unit_type = r.unit_type AND us.unit = r.unit
            GROUP BY r.terminal_asset_alias, r.time_bucket
        )
    )
        
    GROUP BY terminal_asset_alias,time_bucket_1h
    ORDER BY terminal_asset_alias,time_bucket_1h
$BODY$;
