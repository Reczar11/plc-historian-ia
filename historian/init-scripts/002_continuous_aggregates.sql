CREATE MATERIALIZED VIEW plc_readings_1min
WITH (timescaledb.continuous) AS
SELECT
 time_bucket('1 minute', time) AS bucket,
 tag_name,
 avg(value) AS avg_value,
 min(value) AS min_value,
 max(value) AS max_value,
 count(*) AS sample_count
FROM plc_readings
GROUP BY bucket, tag_name;

CREATE MATERIALIZED VIEW plc_readings_1hour
WITH (timescaledb.continuous) AS
SELECT
 time_bucket('1 hour', bucket) AS bucket,
 tag_name,
 avg(avg_value) AS avg_value,
 min(min_value) AS min_value,
 max(max_value) AS max_value,
 sum(sample_count) AS sample_count
FROM plc_readings_1min
GROUP BY time_bucket('1 hour', bucket), tag_name;

SELECT add_continuous_aggregate_policy('plc_readings_1min',
 start_offset => INTERVAL '10 minutes',
 end_offset => INTERVAL '1 minute',
 schedule_interval => INTERVAL '1 minute');

SELECT add_continuous_aggregate_policy('plc_readings_1hour',
 start_offset => INTERVAL '3 hours',
 end_offset => INTERVAL '1 hour',
 schedule_interval => INTERVAL '1 hour');
