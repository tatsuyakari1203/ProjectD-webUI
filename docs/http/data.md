# Get Telemetry Data

| Parameter | Value |
|-----------|-------|
| URL | `/api/data` |
| Method | `GET` |

| Query Parameters | Description |
|-----------------|-------------|
| `device_id` | (Optional) Filter by device ID |
| `topic_id` | (Optional) Filter by topic ID |
| `limit` | (Optional) Limit number of results (default: 100) |

## Request

**Headers**
```
X-API-Key: YOUR_API_KEY
```

## Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "device_id": 1,
      "device_name": "esp8266_sensor",
      "topic_id": 1,
      "topic_name": "temperature",
      "payload": {
        "value": 25.3,
        "unit": "celsius",
        "timestamp": 1742593818.614071
      },
      "timestamp": "2023-04-15T10:25:30"
    },
    {
      "id": 2,
      "device_id": 1,
      "device_name": "esp8266_sensor",
      "topic_id": 2,
      "topic_name": "humidity",
      "payload": {
        "value": 68.2,
        "unit": "percent",
        "timestamp": 1742593820.123456
      },
      "timestamp": "2023-04-15T10:25:35"
    }
  ]
}
```
