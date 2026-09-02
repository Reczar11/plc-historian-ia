ALTER TABLE plc_readings SET (
 timescaledb.compress,
 timescaledb.compress_segmentby = 'tag_name'
);
SELECT add_compression_policy('plc_readings', INTERVAL '7 days');

SELECT add_retention_policy('plc_readings', INTERVAL '90 days');
