import json
import threading
import time
from flask import current_app, Flask
import paho.mqtt.client as mqtt

from app import db, create_app
from app.models.relay import Relay
from app.models.sensor import SensorData
from app.models.schedule import IrrigationSchedule
from app.models.log import MqttLog

# Global MQTT client and configs
mqtt_client = None
mqtt_topics = {}
mqtt_api_key = None
flask_app = None

def init_mqtt(app):
    """
    Initialize MQTT client
    """
    global mqtt_client, mqtt_topics, mqtt_api_key, flask_app
    
    # Store app instance for creating app contexts later
    flask_app = app
    
    # Store MQTT configuration in global variables
    mqtt_topics = {
        'sensors': app.config['MQTT_TOPIC_SENSORS'],
        'status': app.config['MQTT_TOPIC_STATUS'],
        'schedule_status': app.config['MQTT_TOPIC_SCHEDULE_STATUS'],
        'control': app.config['MQTT_TOPIC_CONTROL'],
        'schedule': app.config['MQTT_TOPIC_SCHEDULE'],
        'environment': app.config['MQTT_TOPIC_ENVIRONMENT'],
        'logs': app.config['MQTT_TOPIC_LOGS'],
        'logconfig': app.config['MQTT_TOPIC_LOGCONFIG']
    }
    mqtt_api_key = app.config['API_KEY']
    
    # Configure MQTT client
    mqtt_client = mqtt.Client(app.config['MQTT_CLIENT_ID'])
    
    # Set up callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    
    # Connect to broker
    broker_url = app.config['MQTT_BROKER_URL']
    broker_port = app.config['MQTT_BROKER_PORT']
    keepalive = app.config['MQTT_KEEPALIVE']
    
    app.logger.info(f"Connecting to MQTT broker at {broker_url}:{broker_port}")
    
    try:
        mqtt_client.connect(broker_url, broker_port, keepalive)
        
        # Start MQTT loop in a separate thread
        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        
        app.logger.info("MQTT client started successfully")
    except Exception as e:
        app.logger.error(f"Failed to connect to MQTT broker: {e}")

def on_connect(client, userdata, flags, rc):
    """
    Callback for when the client connects to the broker
    """
    global mqtt_topics
    
    if rc == 0:
        print("Connected to MQTT broker")
        
        # Subscribe to topics using stored configuration
        client.subscribe(mqtt_topics['sensors'])
        client.subscribe(mqtt_topics['status'])
        client.subscribe(mqtt_topics['schedule_status'])
        client.subscribe(mqtt_topics['logs'])
        
        print("Subscribed to MQTT topics")
    else:
        print(f"Failed to connect to MQTT broker with code {rc}")

def on_message(client, userdata, msg):
    """
    Callback for when a message is received from the broker
    """
    global mqtt_topics, mqtt_api_key, flask_app
    
    try:
        print(f"Received message on topic: {msg.topic}")
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # Validate API key if present
        api_key = payload.get('api_key')
        if api_key != mqtt_api_key:
            print("Invalid API key in MQTT message")
            return
        
        # Create a new app context if app is not None
        if flask_app is None:
            # Recreate the Flask application if the stored app is None
            print("Creating new Flask app for message processing")
            temp_app = create_app()
            with temp_app.app_context():
                process_mqtt_message(msg.topic, payload)
        else:
            # Use the stored Flask app
            with flask_app.app_context():
                process_mqtt_message(msg.topic, payload)
            
    except json.JSONDecodeError:
        print("Failed to parse MQTT message as JSON")
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def process_mqtt_message(topic, payload):
    """
    Process MQTT message within an app context
    """
    global mqtt_topics
    
    try:
        if topic == mqtt_topics['sensors']:
            process_sensor_data(payload)
        elif topic == mqtt_topics['status']:
            process_relay_status(payload)
        elif topic == mqtt_topics['schedule_status']:
            process_schedule_status(payload)
        elif topic == mqtt_topics['logs']:
            process_log_message(payload)
    except Exception as e:
        print(f"Error processing message for topic {topic}: {e}")

def on_disconnect(client, userdata, rc):
    """
    Callback for when the client disconnects from the broker
    """
    if rc != 0:
        print(f"Unexpected disconnection from MQTT broker with code {rc}")
        time.sleep(5)  # Wait before attempting to reconnect
        try:
            client.reconnect()
        except Exception as e:
            print(f"Failed to reconnect to MQTT broker: {e}")
    else:
        print("Disconnected from MQTT broker")

def process_sensor_data(data):
    """
    Process sensor data from MQTT
    """
    SensorData.from_mqtt_data(data)

def process_relay_status(data):
    """
    Process relay status from MQTT
    """
    Relay.from_mqtt_data(data)

def process_schedule_status(data):
    """
    Process schedule status from MQTT
    """
    IrrigationSchedule.from_mqtt_data(data)

def process_log_message(data):
    """
    Process log message from MQTT
    """
    log_entry = MqttLog.from_mqtt_data(data)
    if log_entry:
        try:
            db.session.add(log_entry)
            db.session.commit()
            # Optional: print to server console as well, or use app.logger
            # print(f"Stored log from ESP32: {data.get('message')}")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving log to database: {e}")
            current_app.logger.error(f"Error saving MQTT log to DB: {e} - Data: {data}")
    else:
        print(f"Failed to create MqttLog object from data: {data}")
        current_app.logger.warning(f"Failed to parse MQTT log data: {data}")

def publish_relay_control(relay_operations):
    """
    Publish relay control message for one or more relays.
    relay_operations: A list of dictionaries, where each dictionary is:
                      {'id': <int>, 'state': <bool>, 'duration': <int_seconds_optional>}
    """
    global mqtt_client, mqtt_topics, mqtt_api_key
    
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False

    if not isinstance(relay_operations, list) or not relay_operations:
        print("Invalid relay_operations: Must be a non-empty list.")
        return False

    processed_relays = []
    for op in relay_operations:
        if not isinstance(op, dict) or 'id' not in op or 'state' not in op:
            print(f"Invalid operation format in relay_operations: {op}")
            continue # Skip malformed operation
        
        relay_payload_item = {
            "id": op['id'],
            "state": op['state']
        }
        
        duration_seconds = op.get('duration', 0)
        if duration_seconds > 0:
            duration_ms = duration_seconds * 1000  # Convert seconds to milliseconds
            relay_payload_item["duration"] = duration_ms
        processed_relays.append(relay_payload_item)

    if not processed_relays:
        print("No valid relay operations to publish after processing.")
        return False
            
    payload = {
        "api_key": mqtt_api_key,
        "relays": processed_relays
    }
    
    try:
        result = mqtt_client.publish(
            mqtt_topics['control'],
            json.dumps(payload),
            qos=1
        )
        print(f"Published relay control: {payload}, Result: {result.rc}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing relay control message: {e}")
        return False

def publish_schedule(schedule):
    """
    Publish schedule message
    """
    global mqtt_client, mqtt_topics, mqtt_api_key
    
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False
    
    # Convert schedule object to dict format expected by MQTT
    task = {
        "id": schedule.id,
        "active": schedule.active,
        "days": schedule.days_list,
        "time": schedule.time,
        "duration": schedule.duration,
        "zones": schedule.zones_list,
        "priority": schedule.priority
    }
    
    # Add sensor condition if available
    if schedule.sensor_condition:
        task["sensor_condition"] = schedule.sensor_condition_dict
    
    payload = {
        "api_key": mqtt_api_key,
        "tasks": [task]
    }
    
    try:
        result = mqtt_client.publish(
            mqtt_topics['schedule'],
            json.dumps(payload),
            qos=1
        )
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing schedule message: {e}")
        return False

def delete_schedule(schedule_id):
    """
    Delete a schedule via MQTT
    """
    global mqtt_client, mqtt_topics, mqtt_api_key
    
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False
    
    payload = {
        "api_key": mqtt_api_key,
        "delete_tasks": [schedule_id]
    }
    
    try:
        result = mqtt_client.publish(
            mqtt_topics['schedule'],
            json.dumps(payload),
            qos=1
        )
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing delete schedule message: {e}")
        return False

def publish_environment_update(data):
    """
    Publish environment update message
    """
    global mqtt_client, mqtt_topics, mqtt_api_key
    
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False
    
    # Add API key to payload
    payload = {
        "api_key": mqtt_api_key
    }
    
    # Add provided data
    payload.update(data)
    
    try:
        result = mqtt_client.publish(
            mqtt_topics['environment'],
            json.dumps(payload),
            qos=1
        )
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing environment update message: {e}")
        return False

def publish_log_config(target, level):
    """
    Publish log configuration message
    """
    global mqtt_client, mqtt_topics, mqtt_api_key
    
    if mqtt_client is None:
        print("MQTT client not initialized for log config")
        return False
    
    payload = {
        # "api_key": mqtt_api_key, # jsondocs.md shows no api_key for logconfig
        "target": target, # "serial" or "mqtt"
        "level": level    # "NONE", "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"
    }
    
    try:
        result = mqtt_client.publish(
            mqtt_topics['logconfig'],
            json.dumps(payload),
            qos=1 # As per jsondocs, most control messages use qos=1
        )
        print(f"Published log config: {payload}, Result: {result.rc}")
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing log configuration message: {e}")
        return False

def is_connected():
    """
    Check if MQTT client is connected
    """
    global mqtt_client
    
    if mqtt_client is None:
        return False
    
    try:
        return mqtt_client.is_connected()
    except Exception:
        return False 