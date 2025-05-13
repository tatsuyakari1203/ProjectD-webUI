# Publish Data

| Parameter | Value |
|-----------|-------|
| URL | `/api/publish` |
| Method | `POST` |
| Content-Type | `application/json` |

## Request

**Headers**
```
Content-Type: application/json
X-API-Key: YOUR_API_KEY
```

**JSON Request Body**
```json
{
  "device": "device_name",
  "topic": "topic_name",
  "payload": {
    "value": 25.3,
    "unit": "celsius",
    "timestamp": 1742593818.614071
  }
}
```

## Response

**Success (200 OK)**
```json
{
  "success": true,
  "message": "Data published successfully"
}
```

**Error (401 Unauthorized)**
```json
{
  "success": false,
  "error": "Invalid API key"
}
```
