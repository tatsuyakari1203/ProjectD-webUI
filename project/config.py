import os
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/irrigation.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MQTT configuration
    MQTT_BROKER_URL = os.environ.get('MQTT_BROKER_URL') or 'iot.karis.cloud'
    MQTT_BROKER_PORT = int(os.environ.get('MQTT_BROKER_PORT') or 1883)
    MQTT_CLIENT_ID = os.environ.get('MQTT_CLIENT_ID') or f'irrigation_web_app_{uuid.uuid4().hex[:12]}'
    MQTT_KEEPALIVE = int(os.environ.get('MQTT_KEEPALIVE') or 60)
    
    # API key for authentication
    API_KEY = os.environ.get('API_KEY') or '8a679613-019f-4b88-9068-da10f09dcdd2'
    
    # MQTT topics
    MQTT_TOPIC_SENSORS = 'irrigation/esp32_6relay/sensors'
    MQTT_TOPIC_CONTROL = 'irrigation/esp32_6relay/control'
    MQTT_TOPIC_STATUS = 'irrigation/esp32_6relay/status'
    MQTT_TOPIC_SCHEDULE = 'irrigation/esp32_6relay/schedule'
    MQTT_TOPIC_SCHEDULE_STATUS = 'irrigation/esp32_6relay/schedule/status'
    MQTT_TOPIC_ENVIRONMENT = 'irrigation/esp32_6relay/environment'
    MQTT_TOPIC_LOGS = 'irrigation/esp32_6relay/logs'
    MQTT_TOPIC_LOGCONFIG = 'irrigation/esp32_6relay/logconfig'
    
    # Data refresh intervals (seconds)
    SENSOR_REFRESH_INTERVAL = 5
    RELAY_STATUS_REFRESH_INTERVAL = 3
    SCHEDULE_STATUS_REFRESH_INTERVAL = 10 