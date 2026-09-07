CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('plant', 'area', 'line', 'equipment')),
    parent_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO assets (id, name, asset_type, parent_id) VALUES
    (1, 'Main Plant', 'plant', NULL),
    (2, 'Production Area', 'area', 1),
    (3, 'Line 1', 'line', 2),
    (4, 'Pump 1', 'equipment', 3);

SELECT setval('assets_id_seq', 4);

ALTER TABLE tags ADD COLUMN asset_id INTEGER REFERENCES assets(id);

UPDATE tags SET asset_id = 4;
