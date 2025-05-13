import json
import threading
import time
from flask import current_app
import paho.mqtt.client as mqtt

from app import db
from app.models.relay import Relay
from app.models.sensor import SensorData
from app.models.schedule import IrrigationSchedule

# Global MQTT client
mqtt_client = None

def init_mqtt(app):
    """
    Initialize MQTT client
    """
    global mqtt_client
    
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
    if rc == 0:
        print("Connected to MQTT broker")
        
        # Subscribe to topics
        client.subscribe(current_app.config['MQTT_TOPIC_SENSORS'])
        client.subscribe(current_app.config['MQTT_TOPIC_STATUS'])
        client.subscribe(current_app.config['MQTT_TOPIC_SCHEDULE_STATUS'])
        
        print("Subscribed to MQTT topics")
    else:
        print(f"Failed to connect to MQTT broker with code {rc}")

def on_message(client, userdata, msg):
    """
    Callback for when a message is received from the broker
    """
    try:
        print(f"Received message on topic: {msg.topic}")
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # Validate API key if present
        api_key = payload.get('api_key')
        if api_key != current_app.config['API_KEY']:
            print("Invalid API key in MQTT message")
            return
        
        # Process message based on topic
        if msg.topic == current_app.config['MQTT_TOPIC_SENSORS']:
            process_sensor_data(payload)
            
        elif msg.topic == current_app.config['MQTT_TOPIC_STATUS']:
            process_relay_status(payload)
            
        elif msg.topic == current_app.config['MQTT_TOPIC_SCHEDULE_STATUS']:
            process_schedule_status(payload)
            
    except json.JSONDecodeError:
        print("Failed to parse MQTT message as JSON")
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

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
    with current_app.app_context():
        SensorData.from_mqtt_data(data)

def process_relay_status(data):
    """
    Process relay status from MQTT
    """
    with current_app.app_context():
        Relay.from_mqtt_data(data)

def process_schedule_status(data):
    """
    Process schedule status from MQTT
    """
    with current_app.app_context():
        IrrigationSchedule.from_mqtt_data(data)

def publish_relay_control(relay_id, state, duration=0):
    """
    Publish relay control message
    """
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False
    
    payload = {
        "api_key": current_app.config['API_KEY'],
        "relays": [
            {
                "id": relay_id,
                "state": state
            }
        ]
    }
    
    # Add duration if provided
    if duration > 0:
        payload["relays"][0]["duration"] = duration
    
    try:
        result = mqtt_client.publish(
            current_app.config['MQTT_TOPIC_CONTROL'],
            json.dumps(payload),
            qos=1
        )
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing relay control message: {e}")
        return False

def publish_schedule(schedule):
    """
    Publish schedule message
    """
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
        "api_key": current_app.config['API_KEY'],
        "tasks": [task]
    }
    
    try:
        result = mqtt_client.publish(
            current_app.config['MQTT_TOPIC_SCHEDULE'],
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
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False
    
    payload = {
        "api_key": current_app.config['API_KEY'],
        "delete_tasks": [schedule_id]
    }
    
    try:
        result = mqtt_client.publish(
            current_app.config['MQTT_TOPIC_SCHEDULE'],
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
    if mqtt_client is None:
        print("MQTT client not initialized")
        return False
    
    # Add API key to payload
    payload = {
        "api_key": current_app.config['API_KEY']
    }
    
    # Add provided data
    payload.update(data)
    
    try:
        result = mqtt_client.publish(
            current_app.config['MQTT_TOPIC_ENVIRONMENT'],
            json.dumps(payload),
            qos=1
        )
        return result.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        print(f"Error publishing environment update message: {e}")
        return False 