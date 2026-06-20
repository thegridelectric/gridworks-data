SELECT add_continuous_aggregate_policy('gridworks.readings_1hr',
  start_offset => INTERVAL '2 days',
  end_offset   => INTERVAL '1 hour',
  schedule_interval => INTERVAL '30 minutes');