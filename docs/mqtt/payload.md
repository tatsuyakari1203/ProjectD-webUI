# Định dạng Payload

Payload phải ở định dạng JSON và **phải chứa API key** để xác thực:

```json
{
  "api_key": "YOUR_API_KEY",
  ... other data fields ...
}
```

Ví dụ về payload hợp lệ:

```json
{
  "api_key": "b6266465-0949-437b-b0bb-3591408501c6",
  "value": 25.3,
  "timestamp": 1742593818.614071,
  "unit": "celsius",
  "sensor_type": "temperature",
  "device_info": {
    "name": "esp8266_sensor",
    "type": "DHT22",
    "firmware": "1.0.0"
  }
}
```

> **Lưu ý:** API key sẽ được loại bỏ khỏi payload trước khi lưu vào cơ sở dữ liệu.

> **Chú ý:** Nếu API key không hợp lệ hoặc không được cung cấp, tin nhắn sẽ bị từ chối.
