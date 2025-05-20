#!/bin/bash

# --- Cấu hình ---
# Thư mục chứa ứng dụng (nơi script này được đặt)
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Đường dẫn đến thư mục virtual environment
VENV_DIR="$APP_DIR/venv"
# Tên file log
LOG_FILE="$APP_DIR/app.log"
# Tên file PID
PID_FILE="$APP_DIR/app.pid"
# Cấu hình Gunicorn
GUNICORN_WORKERS=2 # Số lượng worker process, điều chỉnh tùy theo số CPU cores
GUNICORN_BIND="0.0.0.0:6077" # Địa chỉ IP và port Gunicorn sẽ lắng nghe

# --- Bắt đầu Script ---

echo "$(date) - Starting Flask server..." | tee -a "$LOG_FILE"

# Tạo file log nếu chưa tồn tại
touch "$LOG_FILE"

# Kích hoạt virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    echo "$(date) - Virtual environment activated." | tee -a "$LOG_FILE"
else
    echo "$(date) - ERROR: Virtual environment not found at $VENV_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Export biến môi trường cho Flask (FLASK_ENV=production quan trọng)
export FLASK_ENV=production
# FLASK_APP trỏ đến file run.py (cần thiết cho một số lệnh flask, dù gunicorn dùng run:app)
export FLASK_APP="$APP_DIR/run.py"

# Kiểm tra Gunicorn đã được cài đặt chưa
if ! command -v gunicorn &> /dev/null; then
    echo "$(date) - ERROR: gunicorn command not found. Please install gunicorn." | tee -a "$LOG_FILE"
    exit 1
fi

# Di chuyển vào thư mục ứng dụng
cd "$APP_DIR"

echo "$(date) - Starting Gunicorn server..." | tee -a "$LOG_FILE"
echo "$(date) - Workers: $GUNICORN_WORKERS, Bind: $GUNICORN_BIND" | tee -a "$LOG_FILE"
echo "$(date) - Logging to: $LOG_FILE, PID file: $PID_FILE" | tee -a "$LOG_FILE"

# Chạy Gunicorn ở chế độ nền (daemon)
# run:app trỏ đến biến 'app' trong file 'run.py'
gunicorn --workers "$GUNICORN_WORKERS" \
         --bind "$GUNICORN_BIND" \
         run:app \
         --daemon \
         --pid "$PID_FILE" \
         --access-logfile "$LOG_FILE" \
         --error-logfile "$LOG_FILE" \
         --reload

# Kiểm tra Gunicorn đã khởi động thành công chưa (sau một khoảng trễ nhỏ)
sleep 2
if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
    echo "$(date) - Flask server started successfully with Gunicorn. PID: $(cat "$PID_FILE")" | tee -a "$LOG_FILE"
    echo "Flask server is running in the background."
    echo "Logs are being written to: $LOG_FILE"
    echo "To stop the server, run: kill \$(cat $PID_FILE)"
else
    echo "$(date) - ERROR: Failed to start Gunicorn. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
    # Hiển thị vài dòng cuối của log nếu có lỗi
    tail -n 20 "$LOG_FILE"
    exit 1
fi

exit 0 