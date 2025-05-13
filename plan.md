# Kế hoạch phát triển Hệ thống tưới tự động IoT

## 1. Kiến trúc hệ thống

### Backend
- **Framework**: Python Flask
- **Database**: SQLite với SQLAlchemy ORM
- **Giao tiếp**: 
  - HTTP để lấy dữ liệu
  - MQTT để gửi lệnh (Paho-MQTT)
- **Xác thực API**: Quản lý API Key

### Frontend
- **Framework thiết kế**: Bootstrap 5
- **Giao diện**: Chỉ chế độ tối (Dark mode only)
- **Thành phần UI**: Thiết kế dạng thẻ (Card-based design)
- **JavaScript**: Modern ES6 với fetch API
- **Hiển thị dữ liệu**: Chart.js cho dữ liệu cảm biến

## 2. Cấu trúc cơ sở dữ liệu

### Bảng dữ liệu
1. **Relays** (Rơle)
   - id (Khóa chính)
   - name (Tên vùng tưới tùy chỉnh)
   - state (Trạng thái bật/tắt)
   - remaining_time (Thời gian còn lại, giây)
   - last_updated (Cập nhật lần cuối)

2. **IrrigationSchedules** (Lịch tưới)
   - id (Khóa chính)
   - active (Trạng thái kích hoạt)
   - days (Mảng ngày trong tuần - JSON)
   - time (Thời gian bắt đầu)
   - duration (Thời lượng, phút)
   - zones (Mảng vùng tưới - JSON)
   - priority (Mức ưu tiên)
   - state (Trạng thái: idle, running, completed)
   - next_run (Thời gian chạy kế tiếp)
   - sensor_condition (Điều kiện cảm biến - JSON)

3. **SensorData** (Dữ liệu cảm biến)
   - id (Khóa chính)
   - timestamp (Thời gian)
   - temperature (Nhiệt độ)
   - humidity (Độ ẩm không khí)
   - heat_index (Chỉ số nhiệt)
   - soil_moisture (Độ ẩm đất theo vùng - JSON)
   - rain (Trạng thái mưa)
   - light (Cường độ ánh sáng)

4. **Settings** (Cài đặt)
   - key (Khóa chính)
   - value (Giá trị - JSON)

## 3. Tích hợp API

### Endpoint HTTP (cần phát triển)
- `/api/sensor-data` - Lấy dữ liệu cảm biến mới nhất
- `/api/relay-status` - Lấy trạng thái relay
- `/api/schedules` - Lấy lịch tưới

### MQTT Topics (từ tài liệu)
- Subscribe:
  - `irrigation/esp32_6relay/sensors` - Nhận dữ liệu cảm biến
  - `irrigation/esp32_6relay/status` - Nhận trạng thái relay
  - `irrigation/esp32_6relay/schedule/status` - Nhận trạng thái lịch tưới

- Publish:
  - `irrigation/esp32_6relay/control` - Gửi lệnh điều khiển relay
  - `irrigation/esp32_6relay/schedule` - Gửi lệnh lập lịch tưới
  - `irrigation/esp32_6relay/environment` - Gửi cập nhật điều kiện môi trường

### Xác thực
- Lưu API key trong biến môi trường hoặc bảng cài đặt
- Thêm API key vào tất cả payload MQTT
- Thêm middleware xác thực cho endpoint HTTP

## 4. Cấu trúc thư mục dự án

```
project_root/
├── app/
│   ├── __init__.py             # Khởi tạo ứng dụng Flask
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── relay.py            # Model Relay
│   │   ├── schedule.py         # Model Schedule
│   │   └── sensor.py           # Model Sensor
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── mqtt_service.py     # Xử lý MQTT
│   │   ├── relay_service.py    # Xử lý relay
│   │   ├── schedule_service.py # Xử lý lịch tưới
│   │   └── sensor_service.py   # Xử lý dữ liệu cảm biến
│   ├── routes/                 # Flask Blueprints
│   │   ├── __init__.py
│   │   ├── main.py             # Route chính
│   │   ├── api.py              # API endpoints
│   │   └── auth.py             # Xác thực
│   ├── static/                 # Assets tĩnh
│   │   ├── css/
│   │   │   └── style.css       # CSS tùy chỉnh
│   │   ├── js/
│   │   │   ├── dashboard.js    # Script Dashboard
│   │   │   ├── relays.js       # Script Relay
│   │   │   └── schedules.js    # Script Schedule
│   │   └── img/                # Hình ảnh
│   └── templates/              # Jinja2 templates
│       ├── base.html           # Template cơ sở
│       ├── dashboard.html      # Trang Dashboard
│       ├── relays.html         # Trang quản lý relay
│       ├── schedules.html      # Trang quản lý lịch tưới
│       └── sensors.html        # Trang dữ liệu cảm biến
├── config.py                   # Cấu hình ứng dụng
├── requirements.txt            # Các thư viện cần thiết
├── migrations/                 # Alembic migrations
├── run.py                      # Script khởi chạy ứng dụng
└── instance/                   # Thư mục SQLite
    └── irrigation.db           # Cơ sở dữ liệu SQLite
```

## 5. Các tính năng chính

### Dashboard
- Tổng quan trạng thái hệ thống
- Hiển thị relay đang hoạt động
- Hiển thị điều kiện môi trường
- Nút điều khiển relay nhanh
- Lịch tưới sắp tới
- Dữ liệu cảm biến mới nhất với biểu đồ mini

### Quản lý Relay
- Giao diện điều khiển từng relay
- Kích hoạt thủ công với cài đặt thời lượng
- Hiển thị trạng thái hiện tại
- Lịch sử kích hoạt
- Đặt tên/nhãn cho relay

### Quản lý lịch tưới
- Tạo/chỉnh sửa/xóa lịch tưới
- Xem lịch dạng lịch
- Giao diện cài đặt mức ưu tiên
- Hiển thị xung đột lịch
- Kích hoạt/vô hiệu hóa lịch

### Điều kiện môi trường
- Hiển thị dữ liệu cảm biến với biểu đồ chuỗi thời gian
- Giao diện cập nhật điều kiện thủ công
- Phân tích dữ liệu lịch sử
- Tích hợp thời tiết (tính năng tương lai)

### Quy tắc điều kiện cảm biến
- UI để tạo quy tắc tưới dựa trên cảm biến
- Hiển thị trực quan điều kiện
- Giao diện kiểm tra quy tắc

### Cài đặt
- Cấu hình API
- Tùy chọn hệ thống
- Tùy chỉnh giao diện người dùng
- Tốc độ làm mới dữ liệu

## 6. Quy trình phát triển

### Giai đoạn 1: Thiết lập dự án
- Tạo cấu trúc ứng dụng Flask
- Thiết lập SQLAlchemy với models
- Cấu hình MQTT client
- Tạo templates cơ bản với Bootstrap 5
- Triển khai giao diện dark mode

### Giai đoạn 2: Chức năng cốt lõi
- Triển khai điều khiển relay qua MQTT
- Tạo dashboard cơ bản với trạng thái relay
- Lưu trữ và hiển thị dữ liệu cảm biến
- Triển khai lập lịch cơ bản

### Giai đoạn 3: Tính năng nâng cao
- Hoàn thiện giao diện lịch trình
- Triển khai quy tắc điều kiện cảm biến
- Thêm hiển thị dữ liệu trực quan
- Tạo dashboard chi tiết

### Giai đoạn 4: Hoàn thiện
- Tối ưu hóa truy vấn cơ sở dữ liệu
- Nâng cao UI/UX
- Thêm xử lý lỗi
- Triển khai bộ nhớ đệm khi cần thiết

### Giai đoạn 5: Kiểm thử & Triển khai
- Kiểm thử toàn diện
- Viết tài liệu
- Chuẩn bị triển khai

## 7. Cân nhắc kỹ thuật

- **Xử lý kết nối MQTT**: Logic kết nối lại
- **Đồng bộ hóa dữ liệu**: Giữ cơ sở dữ liệu đồng bộ với trạng thái thiết bị
- **Bảo mật API Key**: Lưu trữ và truyền tải an toàn
- **Cập nhật thời gian thực**: Sử dụng AJAX/websockets cho cập nhật UI
- **Thiết kế responsive**: Đảm bảo tương thích di động
- **Xử lý lỗi**: Xử lý vấn đề kết nối một cách êm mượt
- **Ghi log**: Ghi log toàn diện để khắc phục sự cố

## 8. Công nghệ & Thư viện

### Backend
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **Paho-MQTT**: MQTT client
- **Flask-Migrate**: Database migrations
- **SQLite**: Database

### Frontend
- **Bootstrap 5**: UI framework
- **Chart.js**: Trực quan hóa dữ liệu
- **Font Awesome**: Icons
- **jQuery**: DOM manipulation (nếu cần)
- **Moment.js**: Xử lý thời gian
