# Get Topics

| Parameter | Value |
|-----------|-------|
| URL | `/api/topics` |
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
  "topics": [
    {
      "id": 1,
      "name": "temperature",
      "description": "Temperature readings",
      "created_at": "2023-04-15T10:20:30"
    },
    {
      "id": 2,
      "name": "humidity",
      "description": "Humidity readings",
      "created_at": "2023-04-15T10:20:30"
    }
  ]
}
```
