# Get Devices

| Parameter | Value |
|-----------|-------|
| URL | `/api/devices` |
| Method | `GET` |

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
  "devices": [
    {
      "id": 1,
      "name": "esp8266_sensor",
      "description": "ESP8266 temperature sensor",
      "client_id": 1,
      "last_seen": "2023-04-15T10:30:45",
      "created_at": "2023-04-15T10:20:30"
    },
    {
      "id": 2,
      "name": "raspberry_pi",
      "description": "Raspberry Pi with camera",
      "client_id": 1,
      "last_seen": "2023-04-15T10:35:12",
      "created_at": "2023-04-15T10:20:30"
    }
  ]
}
```
