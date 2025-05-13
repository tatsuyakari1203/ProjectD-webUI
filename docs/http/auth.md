# Xác thực

Tất cả các yêu cầu API phải được xác thực bằng API key. Có hai cách để cung cấp API key:

1. **Header (khuyến nghị)**
   ```
   X-API-Key: YOUR_API_KEY
   ```

2. **Query Parameter**
   ```
   ?api_key=YOUR_API_KEY
   ```

> **Cảnh báo:** Nên sử dụng header thay vì query parameter để tránh API key bị lộ trong các log files và URL.
