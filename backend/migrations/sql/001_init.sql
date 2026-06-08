-- AquaWatch initial schema
CREATE TABLE IF NOT EXISTS cameras (
    id VARCHAR PRIMARY KEY,
    location_name VARCHAR,
    lat FLOAT,
    lng FLOAT,
    zone_polygon JSON,
    disappear_threshold INT DEFAULT 15,
    is_active BOOLEAN DEFAULT TRUE,
    last_heartbeat TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR REFERENCES cameras(id),
    track_id INT,
    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    status VARCHAR DEFAULT 'active',
    resolved_by VARCHAR,
    last_position_x INT,
    last_position_y INT,
    disappear_duration_seconds FLOAT,
    thumbnail_path VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON alerts(triggered_at);
CREATE INDEX IF NOT EXISTS idx_alerts_camera_id ON alerts(camera_id);
CREATE INDEX IF NOT EXISTS idx_alerts_camera_status_triggered
  ON alerts(camera_id, status, triggered_at);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'lifeguard',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Default users (password: 'aquawatch' — change in production!)
-- Hash generated via werkzeug.security.generate_password_hash('aquawatch')
INSERT INTO users (username, password_hash, role) VALUES
  ('admin', 'scrypt:32768:8:1$gKFCZduMxbFx3u9w$62f3d15d1190de585032a210a5ef1bf5718b32ccd8d68092f7c0dddf58bec1a0bad406bb82f1a613f2886030ed83917bd5f56e0e9b4cf90e8dd2c56a71ad83e1', 'admin'),
  ('lifeguard1', 'scrypt:32768:8:1$gKFCZduMxbFx3u9w$62f3d15d1190de585032a210a5ef1bf5718b32ccd8d68092f7c0dddf58bec1a0bad406bb82f1a613f2886030ed83917bd5f56e0e9b4cf90e8dd2c56a71ad83e1', 'lifeguard')
ON CONFLICT (username) DO NOTHING;
