CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    plc_address TEXT,
    data_type TEXT NOT NULL DEFAULT 'REAL',
    engineering_unit TEXT,
    alarm_low DOUBLE PRECISION,
    alarm_high DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO tags (name, plc_address, data_type, engineering_unit, alarm_low, alarm_high) VALUES
    ('Temperature', NULL, 'REAL', 'F', 45.0, 95.0),
    ('Pressure', NULL, 'REAL', 'bar', 2.0, 8.5),
    ('Vibration', NULL, 'REAL', 'mm/s', 0.4, 5.0),
    ('MotorCurrent', NULL, 'REAL', 'A', 8.0, 22.0);
