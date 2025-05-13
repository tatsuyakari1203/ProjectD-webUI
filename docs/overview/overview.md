# Tổng quan

IoT Data Server cung cấp hai phương thức để gửi dữ liệu từ thiết bị IoT tới máy chủ:

1. **MQTT Protocol** - Giao thức nhẹ, tiết kiệm năng lượng, phù hợp với các thiết bị IoT
2. **HTTP REST API** - Dễ sử dụng, tương thích rộng rãi với nhiều nền tảng

Cả hai phương thức đều yêu cầu API key để xác thực yêu cầu. API key được tạo khi bạn đăng ký client mới trong hệ thống và phải được đính kèm trong mọi yêu cầu.

> **Lưu ý:** Trong môi trường sản xuất, hãy đảm bảo giao tiếp qua HTTPS hoặc sử dụng MQTT với TLS để bảo vệ API key của bạn.
