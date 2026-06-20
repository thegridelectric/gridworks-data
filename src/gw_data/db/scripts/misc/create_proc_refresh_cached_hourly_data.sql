CREATE OR REPLACE PROCEDURE gridworks.refresh_cached_hourly_data(job_id int, config jsonb)
LANGUAGE plpgsql
AS $$
DECLARE
    t_start timestamp with time zone := now() - INTERVAL '2 days';
    t_start_valid timestamp with time zone := t_start + INTERVAL '1 hour';
    t_end   timestamp with time zone := now();
BEGIN
    DELETE FROM gridworks.cached_hourly_data
    WHERE time_bucket >= t_start_valid AND time_bucket <= t_end;

    INSERT INTO gridworks.cached_hourly_data
    WITH hourly_data AS MATERIALIZED (
        SELECT * FROM gridworks.calc_hourly_data(t_start => t_start, t_end => t_end)
    )
    SELECT * FROM hourly_data
    WHERE time_bucket >= t_start_valid;
END;
$$;

