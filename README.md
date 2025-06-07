# IOT API 

## API 說明

### 1. POST `/sensor_data`
**功能**: 接收感測器數據並儲存到資料庫。

**範例請求**:
```URL
https://iot.dinochou.dev/sensor_data
```

**方法**: `POST`

**請求 Body**:
```json
{
    "device_id": "your_mobile_device_unique_id",
    "TimeStamp": "2025-04-24T15:46:00+08:00",
    "accel_x": 1.23,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.03
}
```

**範例請求 (使用 `curl`)**:
```bash
curl -X POST https://iot.dinochou.dev/sensor_data \
-H "Content-Type: application/json" \
-d '{
    "device_id": "abc123",
    "TimeStamp": "2025-04-24T15:46:00+08:00",
    "accel_x": 1.23,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.03
}'
```

**回應**:
- 成功: `201 Created`
- 錯誤: `400 Bad Request` 或 `500 Internal Server Error`

---

### 2. GET `/sensor_data`
**功能**: 從資料庫中查詢感測器數據，支援根據 `device_id` 和 `timestamp` 篩選。

**範例請求**:
1. 查詢特定裝置的數據：
   ```URL
   https://iot.dinochou.dev/sensor_data?device_id=abc123
   ```

2. 查詢特定時間之後的數據：
   ```URL
   https://iot.dinochou.dev/sensor_data?start_timestamp=2025-04-01T00:00:00Z
   ```

3. 查詢特定裝置在特定時間範圍內的數據：
   ```URL
   https://iot.dinochou.dev/sensor_data?device_id=abc123&start_timestamp=2025-04-01T00:00:00Z&end_timestamp=2025-04-30T23:59:59Z
   ```

**方法**: `GET`

**支援的篩選條件**:
- `device_id` (選填): 篩選特定裝置的數據。
- `start_timestamp` (選填): 篩選大於或等於此時間的數據。
- `end_timestamp` (選填): 篩選小於或等於此時間的數據。

**回應**:
- 成功: `200 OK`，回傳 JSON 格式的數據列表。
- 錯誤: `400 Bad Request` 或 `500 Internal Server Error`

**範例回應**:
```json
[
    {
        "id": 1,
        "device_id": "abc123",
        "mobile_timestamp": "2025-04-01T12:00:00Z",
        "accel_x": 1.23,
        "accel_y": -0.45,
        "accel_z": 9.81,
        "gyro_x": 0.01,
        "gyro_y": -0.02,
        "gyro_z": 0.03
    },
    {
        "id": 2,
        "device_id": "abc123",
        "mobile_timestamp": "2025-04-02T12:00:00Z",
        "accel_x": 1.25,
        "accel_y": -0.40,
        "accel_z": 9.80,
        "gyro_x": 0.02,
        "gyro_y": -0.01,
        "gyro_z": 0.04
    }
]
```

---

### 3. Health Check `/health`
**功能**: 提供健康檢查 API。

**範例請求**:
```URL
https://iot.dinochou.dev/health
```

**方法**: `GET`

**回應**:
- 成功: `200 OK`
```json
{
    "status": "ok"
}
```

---

### 4. Ping `/ping`
**功能**: 測試 API 是否正常運作。

**範例請求**:
```URL
https://iot.dinochou.dev/ping
```

**方法**: `GET`

**回應**:
- 成功: `200 OK`
```json
{
    "message": "pong"
}
```

---

### 5. Inference `/inference?end-timestamp{timestamp}&device-id={device_id}`
**功能**: 輸入要查找的時間點，找到在那之前一秒內的擊球事件與球速。

**範例請求**:
```URL
https://iot.dinochou.dev/inference?end-timestamp=2025-05-13%2015:51:09.600096
```

**方法**: `GET`

**回應**:
- 成功: `200 OK`，回傳 JSON 格式的數據列表。
- 錯誤: `400 Bad Request` , `500 Internal Server Error`, `500 讀取數據時發生錯誤`

**範例回應**:
```json
[
    {"classification_prediction":["Clear"],"speed_prediction":[[70.0]]}
]
```

### 6. POST `/inferencebydata`
**功能**: post一包json數據，回傳球種與球速。

**方法**: `POST`

**請求 Body範例**:
```json
[
  {
    "accel_x": 0.12,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00
  },
  {
    "accel_x": 0.13,
    "accel_y": -0.50,
    "accel_z": 9.79,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.14,
    "accel_y": 5.23,
    "accel_z": 9.80,
    "gyro_x": 0.02,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.11,
    "accel_y": 15.88,
    "accel_z": 9.76,
    "gyro_x": 0.03,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.09,
    "accel_y": 0.35,
    "accel_z": 9.78,
    "gyro_x": 0.02,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.12,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00
  },
  {
    "accel_x": 0.13,
    "accel_y": -0.50,
    "accel_z": 9.79,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.14,
    "accel_y": 5.23,
    "accel_z": 9.80,
    "gyro_x": 0.02,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.11,
    "accel_y": 15.88,
    "accel_z": 9.76,
    "gyro_x": 0.03,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.09,
    "accel_y": 0.35,
    "accel_z": 9.78,
    "gyro_x": 0.02,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.12,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00
  },
  {
    "accel_x": 0.13,
    "accel_y": -0.50,
    "accel_z": 9.79,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.14,
    "accel_y": 5.23,
    "accel_z": 9.80,
    "gyro_x": 0.02,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.11,
    "accel_y": 15.88,
    "accel_z": 9.76,
    "gyro_x": 0.03,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.09,
    "accel_y": 0.35,
    "accel_z": 9.78,
    "gyro_x": 0.02,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.12,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00
  },
  {
    "accel_x": 0.13,
    "accel_y": -0.50,
    "accel_z": 9.79,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.14,
    "accel_y": 5.23,
    "accel_z": 9.80,
    "gyro_x": 0.02,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.11,
    "accel_y": 15.88,
    "accel_z": 9.76,
    "gyro_x": 0.03,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.09,
    "accel_y": 0.35,
    "accel_z": 9.78,
    "gyro_x": 0.02,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.12,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00
  },
  {
    "accel_x": 0.13,
    "accel_y": -0.50,
    "accel_z": 9.79,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.14,
    "accel_y": 5.23,
    "accel_z": 9.80,
    "gyro_x": 0.02,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.11,
    "accel_y": 15.88,
    "accel_z": 9.76,
    "gyro_x": 0.03,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.09,
    "accel_y": 0.35,
    "accel_z": 9.78,
    "gyro_x": 0.02,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.12,
    "accel_y": -0.45,
    "accel_z": 9.81,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00
  },
  {
    "accel_x": 0.13,
    "accel_y": -0.50,
    "accel_z": 9.79,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  },
  {
    "accel_x": 0.14,
    "accel_y": 5.23,
    "accel_z": 9.80,
    "gyro_x": 0.02,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.11,
    "accel_y": 15.88,
    "accel_z": 9.76,
    "gyro_x": 0.03,
    "gyro_y": -0.01,
    "gyro_z": 0.02
  },
  {
    "accel_x": 0.09,
    "accel_y": 0.35,
    "accel_z": 9.78,
    "gyro_x": 0.02,
    "gyro_y": -0.02,
    "gyro_z": 0.01
  }
]
```

**回應**:
- 成功: `200 OK`, 回應JSON格式的球種與球速
- 錯誤: `400 Bad Request` 或 `500 Internal Server Error` 或 `404 Not Found`

---
