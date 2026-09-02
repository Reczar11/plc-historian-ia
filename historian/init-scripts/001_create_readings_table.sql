CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE plc_readings (
 time TIMESTAMPTZ NOT NULL,
 tag_name TEXT NOT NULL,
 value DOUBLE PRECISION,
 quality TEXT
);

SELECT create_hypertable('plc_readings', 'time');
CREATE INDEX ON plc_readings (tag_name, time DESC);
