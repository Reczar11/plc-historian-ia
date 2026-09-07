CREATE TABLE alarm_events (
    id SERIAL PRIMARY KEY,
    tag_name TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    limit_type TEXT NOT NULL CHECK (limit_type IN ('low', 'high')),
    limit_value DOUBLE PRECISION NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    cleared_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cleared')),
    acknowledged BOOLEAN NOT NULL DEFAULT false,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX ON alarm_events (tag_name, status);
