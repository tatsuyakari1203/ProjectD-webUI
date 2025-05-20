from app import db
from datetime import datetime

class MqttLog(db.Model):
    __tablename__ = 'mqtt_logs'

    id = db.Column(db.Integer, primary_key=True)
    # ESP32 might send timestamp as unix timestamp or ms since boot.
    # We will store it as datetime object in UTC.
    device_timestamp_str = db.Column(db.String(50), nullable=True) # Original timestamp string from device
    server_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    level_num = db.Column(db.Integer, nullable=True)
    level_str = db.Column(db.String(10), nullable=True) # CRITICAL, ERROR, INFO, DEBUG
    tag = db.Column(db.String(50), nullable=True) # Module/component tag
    message = db.Column(db.Text, nullable=False)
    core_id = db.Column(db.Integer, nullable=True)
    free_heap = db.Column(db.Integer, nullable=True)
    # For performance logs
    log_type = db.Column(db.String(20), nullable=True) # e.g., 'performance'
    event_name = db.Column(db.String(50), nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, nullable=True)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<MqttLog {self.id} [{self.level_str}] {self.tag}: {self.message[:50]}>'

    def to_dict(self):
        return {
            'id': self.id,
            'device_timestamp_str': self.device_timestamp_str,
            'server_timestamp': self.server_timestamp.isoformat() if self.server_timestamp else None,
            'level_num': self.level_num,
            'level_str': self.level_str,
            'tag': self.tag,
            'message': self.message,
            'core_id': self.core_id,
            'free_heap': self.free_heap,
            'log_type': self.log_type,
            'event_name': self.event_name,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'details': self.details
        }

    @staticmethod
    def from_mqtt_data(data):
        if not data or not isinstance(data, dict):
            return None

        # Basic log fields
        new_log = MqttLog(
            device_timestamp_str=str(data.get('timestamp')), # Store original as string
            level_num=data.get('level_num'),
            level_str=data.get('level_str'),
            tag=data.get('tag'),
            message=data.get('message', 'No message content'), # Ensure message is not null
            core_id=data.get('core_id'),
            free_heap=data.get('free_heap')
        )

        # Performance log specific fields
        if data.get('type') == 'performance':
            new_log.log_type = 'performance'
            new_log.event_name = data.get('event_name')
            new_log.duration_ms = data.get('duration_ms')
            new_log.success = data.get('success')
            new_log.details = data.get('details')
        
        # Add to session and commit by the caller in mqtt_service within app_context
        return new_log 