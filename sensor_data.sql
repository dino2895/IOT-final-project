CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL, -- 裝置唯一識別碼
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'utc'), -- 伺服器接收時間 (UTC)
    mobile_timestamp TIMESTAMP WITHOUT TIME ZONE, -- 手機端發送的時間戳記 (建議為 UTC)
    accel_x REAL NOT NULL,
    accel_y REAL NOT NULL,
    accel_z REAL NOT NULL,
    gyro_x REAL NOT NULL,
    gyro_y REAL NOT NULL,
    gyro_z REAL NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (now() AT TIME ZONE 'utc') -- 資料記錄在資料庫中的時間
);

-- 為了加速查詢特定裝置的數據，可以建立索引
CREATE INDEX idx_device_id_timestamp ON sensor_data (device_id, timestamp DESC);

-- 如果你需要根據手機端時間戳記進行查詢，可以建立這個索引
CREATE INDEX idx_mobile_timestamp ON sensor_data (mobile_timestamp DESC);