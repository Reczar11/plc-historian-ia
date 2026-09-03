CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('operator', 'engineer', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO users (username, password_hash, role) VALUES
    ('admin', '$2b$12$n6a32I4DD7U8Hfeyv4Wqr.SWy6mrHhrQwlrRHxRkpS30jw3z/VZsW', 'admin');
