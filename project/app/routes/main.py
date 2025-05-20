from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from app.models.relay import Relay
from app.models.sensor import SensorData
from app.models.schedule import IrrigationSchedule
from app.models.settings import Settings
from app.models.log import MqttLog
from app.services.mqtt_service import publish_relay_control
from app import db
import json
import os
import sqlite3
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Dashboard page
    """
    # Get latest sensor data
    sensor_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    # Get all relays
    relays = Relay.query.all()
    
    # Get active schedules (sorted by next_run)
    schedules = IrrigationSchedule.query.filter_by(active=True).order_by(IrrigationSchedule.next_run).all()
    
    # Get schedules that are currently running
    running_schedules = IrrigationSchedule.query.filter_by(state='running').all()
    
    return render_template(
        'dashboard.html',
        sensor_data=sensor_data,
        relays=relays,
        schedules=schedules,
        running_schedules=running_schedules,
        title='Dashboard'
    )

@main_bp.route('/relays')
def relays():
    """
    Relay management page
    """
    relays = Relay.query.all()
    return render_template('relays.html', relays=relays, title='Relay Management')

@main_bp.route('/relay/control', methods=['POST'])
def relay_control():
    """
    Handle relay control actions
    """
    relay_id = request.form.get('relay_id', type=int)
    action = request.form.get('action')
    # Duration from form is optional, default to 0 if not provided or empty
    duration_str = request.form.get('duration', '')
    duration = 0
    if duration_str.isdigit():
        duration = int(duration_str)
    
    if relay_id is None or not action: # Check relay_id for None explicitly
        flash('Invalid request: Missing relay ID or action', 'danger')
        return redirect(url_for('main.relays'))
    
    relay = Relay.query.get_or_404(relay_id)
    
    # Determine the state based on action
    if action == 'on':
        state = True
        # Duration is taken from form, or defaults to 0 if not provided
    elif action == 'on_no_duration':
        state = True
        duration = 0 # Explicitly set duration to 0 for this action
    elif action == 'off':
        state = False
        duration = 0 # Duration is not applicable when turning off
    else:
        flash('Invalid action', 'danger')
        return redirect(url_for('main.relays'))
    
    # Package the operation into a list
    relay_operation = {
        'id': relay_id,
        'state': state
    }
    if duration > 0 and state: # Only add duration if turning on and duration is positive
        relay_operation['duration'] = duration

    operations_list = [relay_operation]
    
    # Publish relay control command
    if publish_relay_control(operations_list):
        flash(f'Relay {relay.name} (ID: {relay_id}) command ({action.upper()}) sent.', 'success')
    else:
        flash(f'Failed to send command for relay {relay.name} (ID: {relay_id}).', 'danger')
    
    return redirect(url_for('main.relays'))

@main_bp.route('/schedules')
def schedules():
    """
    Schedule management page
    """
    schedules = IrrigationSchedule.query.order_by(IrrigationSchedule.next_run).all()
    relays = Relay.query.all()
    return render_template('schedules.html', schedules=schedules, relays=relays, title='Schedule Management')

@main_bp.route('/sensors')
def sensors():
    """
    Sensor data page
    """
    latest_sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    # sensor_history for charts is fetched by API, so not directly processed here for template display.

    primary_soil_moisture_value = None
    primary_soil_moisture_unit = None
    # For values displayed directly in the top cards (if not using latest_sensor.field directly in template)
    display_temperature = None
    display_humidity = None
    # heat_index is not directly displayed in top cards anymore, so no specific variable needed here for it.
    light_level_value = None
    light_level_timestamp = None

    def get_sensor_field(sensor_obj, field_name):
        field_data = getattr(sensor_obj, field_name, None)
        if isinstance(field_data, str):
            try:
                return json.loads(field_data)
            except json.JSONDecodeError:
                current_app.logger.error(f"Failed to parse JSON for {field_name}: {field_data}")
                return None
        return field_data

    if latest_sensor:
        temp_data = get_sensor_field(latest_sensor, 'temperature')
        if isinstance(temp_data, dict):
            display_temperature = temp_data.get('value')
        elif temp_data is not None: # If it's a direct numeric value after get_sensor_field
            display_temperature = temp_data

        hum_data = get_sensor_field(latest_sensor, 'humidity')
        if isinstance(hum_data, dict):
            display_humidity = hum_data.get('value')
        elif hum_data is not None:
            display_humidity = hum_data
            
        # Primary Soil Moisture (for the dedicated card)
        soil_data = get_sensor_field(latest_sensor, 'soil_moisture')
        if isinstance(soil_data, dict):
            primary_soil_moisture_value = soil_data.get('value')
            primary_soil_moisture_unit = soil_data.get('unit')
        # Fallback for primary_soil_moisture_value/unit if they are direct attributes (less likely now)
        elif hasattr(latest_sensor, 'primary_soil_moisture_value'):
            primary_soil_moisture_value = getattr(latest_sensor, 'primary_soil_moisture_value', None)
            primary_soil_moisture_unit = getattr(latest_sensor, 'primary_soil_moisture_unit', None)

        # Light Level
        light_data_full = get_sensor_field(latest_sensor, 'light')
        if isinstance(light_data_full, dict):
            light_level_value = light_data_full.get('value')
            light_level_timestamp = light_data_full.get('timestamp', latest_sensor.timestamp if latest_sensor else None)
        elif light_data_full is not None: # If light data is just the value
            light_level_value = light_data_full
            light_level_timestamp = latest_sensor.timestamp if latest_sensor else None
        
        # Zoned soil moisture - this part is still speculative as payload doesn't show it
        soil_moisture_zones_list = []
        # zoned_soil_data_str = get_sensor_field(latest_sensor, 'soil_moisture_zones') # Example if it was a field named 'soil_moisture_zones'
        # if isinstance(zoned_soil_data_str, dict): # Or if it was already a dict
        #     for zone_id, value in zoned_soil_data_str.items():
        #         # ... append to soil_moisture_zones_list ...

    api_key = Settings.get('api_key', current_app.config['API_KEY'])
    
    # Note: latest_sensor object is passed directly, template uses its attributes for Temp, Humidity, Rain.
    # We are preparing primary_soil_moisture_value/unit and light_level specifically.
    return render_template(
        'sensors.html', 
        latest_sensor=latest_sensor, # Passed for direct access in template for some fields
        # sensor_history=sensor_history, # Not used directly in template rendering
        soil_moisture_zones_list=soil_moisture_zones_list, # For the zones table
        primary_soil_moisture_value=primary_soil_moisture_value,
        primary_soil_moisture_unit=primary_soil_moisture_unit,
        display_temperature=display_temperature, # For template if it stops using latest_sensor.temperature directly
        display_humidity=display_humidity,     # For template if it stops using latest_sensor.humidity directly
        light_level_value=light_level_value,
        light_level_timestamp=light_level_timestamp,
        settings={'api_key': api_key},
        config=current_app.config,
        title='Sensor Data'
    )

@main_bp.route('/settings')
def settings():
    """
    Settings page
    """
    # Get application settings from database
    app_settings = {
        'api_key': Settings.get('api_key', current_app.config['API_KEY']),
        'mqtt_broker': Settings.get('mqtt_broker', current_app.config['MQTT_BROKER_URL']),
        'mqtt_port': Settings.get('mqtt_port', current_app.config['MQTT_BROKER_PORT']),
        'notifications': {
            'enabled': Settings.get('notifications_enabled', False),
            'email': Settings.get('notification_email', ''),
            'events': {
                'schedule_start': Settings.get('notify_schedule_start', True),
                'schedule_end': Settings.get('notify_schedule_end', True),
                'errors': Settings.get('notify_errors', True),
                'sensor_alerts': Settings.get('notify_sensor_alerts', False)
            }
        },
        'data': {
            'retention': Settings.get('data_retention', 30),
            'sensor_interval': Settings.get('sensor_update_interval', 
                                           current_app.config['SENSOR_REFRESH_INTERVAL']),
            'status_interval': Settings.get('status_update_interval',
                                           current_app.config['RELAY_STATUS_REFRESH_INTERVAL'])
        }
    }
    
    # Get database stats
    db_stats = get_database_stats()
    
    return render_template(
        'settings.html', 
        settings=app_settings, 
        db_stats=db_stats,
        title='Settings'
    )

def get_database_stats():
    """
    Get database statistics
    """
    stats = {
        'size': 0,
        'sensor_records': 0,
        'mqtt_status': 'Disconnected'
    }
    
    # Get database file path
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    if not db_path.startswith('/'):
        db_path = os.path.join(current_app.instance_path, db_path)
    
    # Get file size
    try:
        stats['size'] = os.path.getsize(db_path) / (1024 * 1024)  # Convert to MB
    except (OSError, FileNotFoundError):
        stats['size'] = 0
    
    # Get sensor record count
    stats['sensor_records'] = SensorData.query.count()
    
    # Check MQTT connection status
    from app.services.mqtt_service import is_connected
    if is_connected():
        stats['mqtt_status'] = 'Connected'
    
    return stats

@main_bp.route('/settings/save', methods=['POST'])
def save_settings():
    """
    Save settings
    """
    try:
        form_data = request.form
        
        # API Configuration
        Settings.set('api_key', form_data.get('apiKey'))
        Settings.set('mqtt_broker', form_data.get('mqttBroker'))
        Settings.set('mqtt_port', int(form_data.get('mqttPort', 1883)))
        
        # Notification Settings
        Settings.set('notifications_enabled', form_data.get('enableNotifications') == 'on')
        Settings.set('notification_email', form_data.get('notificationEmail', ''))
        Settings.set('notify_schedule_start', form_data.get('notifyScheduleStart') == 'on')
        Settings.set('notify_schedule_end', form_data.get('notifyScheduleEnd') == 'on')
        Settings.set('notify_errors', form_data.get('notifyErrors') == 'on')
        Settings.set('notify_sensor_alerts', form_data.get('notifySensorAlerts') == 'on')
        
        # Data Management
        Settings.set('data_retention', int(form_data.get('dataRetention', 30)))
        Settings.set('sensor_update_interval', int(form_data.get('sensorUpdateInterval', 5)))
        Settings.set('status_update_interval', int(form_data.get('statusUpdateInterval', 10)))
        
        flash('Settings saved successfully', 'success')
    except Exception as e:
        flash(f'Error saving settings: {str(e)}', 'danger')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/settings/prune', methods=['POST'])
def prune_database():
    """
    Prune old data from database
    """
    try:
        # Get retention period
        days = Settings.get('data_retention', 30)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old sensor data
        deleted = SensorData.query.filter(SensorData.timestamp < cutoff_date).delete()
        db.session.commit()
        
        flash(f'Successfully pruned {deleted} old sensor records', 'success')
    except Exception as e:
        flash(f'Error pruning database: {str(e)}', 'danger')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/settings/reset', methods=['POST'])
def reset_database():
    """
    Reset database
    """
    try:
        # Delete all sensor data
        SensorData.query.delete()
        
        # Reset schedules but keep configuration
        for schedule in IrrigationSchedule.query.all():
            schedule.state = 'idle'
            schedule.next_run = None
            schedule.calculate_next_run()
        
        # Reset relay states
        for relay in Relay.query.all():
            relay.state = False
            relay.remaining_time = 0
        
        db.session.commit()
        
        flash('Database reset successfully', 'success')
    except Exception as e:
        flash(f'Error resetting database: {str(e)}', 'danger')
    
    return redirect(url_for('main.settings'))

@main_bp.route('/logs')
def device_logs():
    """
    Display device logs from MQTT.
    """
    # Fetch initial logs for template rendering (or let JS handle it all)
    # For simplicity, JS will handle fetching via API
    return render_template('logs.html', title='Device Logs') 