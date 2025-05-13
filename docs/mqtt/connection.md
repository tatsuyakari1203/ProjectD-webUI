# Kết nối MQTT với NanoMQ

Để kết nối với broker NanoMQ, sử dụng các thông số sau:

| Parameter | Value |
|-----------|-------|
| Broker Host | `{{ server_host }}` |
| Broker Port | `1883` (MQTT) hoặc `8083` (WebSocket) hoặc `8883` (MQTT over TLS) |
| Username | Không yêu cầu (Anonymous được bật) |
| Password | Không yêu cầu (Anonymous được bật) |

> **Lưu ý:** Trong môi trường sản xuất, bạn nên tắt Anonymous và cấu hình xác thực người dùng.
