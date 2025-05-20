from flask import Blueprint, jsonify, request, current_app
from app.models.relay import Relay
from app.models.sensor import SensorData
from app.models.schedule import IrrigationSchedule
from app.models.settings import Settings
from app.models.log import MqttLog
from app.models.preset import RelayPreset
from app.services.mqtt_service import publish_relay_control, publish_schedule, delete_schedule, publish_environment_update, publish_log_config
from app import db
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

# Helper function to check API key
def check_api_key():
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key != current_app.config['API_KEY']:
        return False
    return True

@api_bp.before_request
def check_auth():
    """
    Check API key before processing requests
    """
    if not check_api_key():
        return jsonify({'success': False, 'error': 'Invalid API key'}), 401

@api_bp.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    """
    Get latest sensor data
    """
    # Get latest sensor data
    sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    if not sensor:
        return jsonify({'success': False, 'error': 'No sensor data available'}), 404
    
    return jsonify({'success': True, 'data': sensor.to_dict()})

@api_bp.route('/sensor-data/history', methods=['GET'])
def get_sensor_history():
    """
    Get sensor data history
    """
    hours = request.args.get('hours', default=24, type=int)
    start_time = datetime.utcnow() - timedelta(hours=hours)
    sensors = SensorData.query.filter(
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp).all()

    def get_value_from_sensor_field(sensor_attr_value):
        if isinstance(sensor_attr_value, str):
            try:
                loaded_json = json.loads(sensor_attr_value)
                return loaded_json.get('value') if isinstance(loaded_json, dict) else None
            except json.JSONDecodeError:
                return None
        elif isinstance(sensor_attr_value, dict):
            return sensor_attr_value.get('value')
        # If it's already a direct numerical value or None
        return sensor_attr_value 

    response = {
        'success': True,
        'data': [s.to_dict() for s in sensors], # CRITICAL: s.to_dict() must provide primary_soil_moisture_value/unit
        'timestamps': [s.timestamp.isoformat() if s.timestamp else None for s in sensors],
        'temperature': [get_value_from_sensor_field(s.temperature) for s in sensors],
        'humidity': [get_value_from_sensor_field(s.humidity) for s in sensors],
        'heat_index': [get_value_from_sensor_field(s.heat_index) for s in sensors],
        'primary_soil_moisture_value': [],
        'primary_soil_moisture_unit': None,
        'rain': [s.rain for s in sensors], # Assuming s.rain is a direct boolean
        'soil_moisture_zones': {} # For zoned data chart, if re-implemented
    }

    if sensors:
        first_sensor_soil_field = getattr(sensors[0], 'soil_moisture', None)
        if isinstance(first_sensor_soil_field, str):
            try: first_sensor_soil_field = json.loads(first_sensor_soil_field)
            except: first_sensor_soil_field = None
        
        if isinstance(first_sensor_soil_field, dict):
            response['primary_soil_moisture_unit'] = first_sensor_soil_field.get('unit')
        elif hasattr(sensors[0], 'primary_soil_moisture_unit'): # Fallback
            response['primary_soil_moisture_unit'] = getattr(sensors[0], 'primary_soil_moisture_unit', None)

        for s in sensors:
            current_sensor_soil_field = getattr(s, 'soil_moisture', None)
            value_to_append = None
            if isinstance(current_sensor_soil_field, str):
                try: current_sensor_soil_field = json.loads(current_sensor_soil_field)
                except: current_sensor_soil_field = None
            
            if isinstance(current_sensor_soil_field, dict):
                value_to_append = current_sensor_soil_field.get('value')
            elif hasattr(s, 'primary_soil_moisture_value'): # Fallback
                value_to_append = getattr(s, 'primary_soil_moisture_value', None)
            response['primary_soil_moisture_value'].append(value_to_append)
    
    # Logic for 'soil_moisture_zones' chart data would go here if it's re-introduced
    # and if s.to_dict() or another attribute provides this zoned data.

    return jsonify(response)

@api_bp.route('/relay-status', methods=['GET'])
def get_relay_status():
    """
    Get status of all relays
    """
    relays = Relay.query.all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in relays]
    })

@api_bp.route('/relay-control', methods=['POST'])
def relay_control():
    """
    Control relay state
    """
    data = request.json
    
    # API can accept a single relay operation or a list of operations
    # For simplicity, we'll demonstrate handling a single operation first,
    # consistent with how the main.py route works. 
    # To handle multiple, data['relays'] could be a list.

    if not data:
        return jsonify({'success': False, 'error': 'Invalid request data, missing payload.'}), 400

    # Assuming the payload is for a single relay operation for now
    # e.g., {"relay_id": 1, "state": true, "duration": 30}
    # Or, to support batch: {"relays": [{"id":1, "state":true}, {"id":2, "state":false}]}
    # For now, we stick to single relay operation from API to match prior behavior simplify this step.

    if 'relay_id' not in data or 'state' not in data:
        return jsonify({'success': False, 'error': 'Invalid request data: relay_id and state are required.'}), 400
    
    relay_id = data.get('relay_id')
    state = data.get('state')
    duration = data.get('duration', 0) # Duration in seconds, optional
    
    # Validate relay_id type if necessary (e.g., expect int)
    if not isinstance(relay_id, int) or not isinstance(state, bool):
        return jsonify({'success': False, 'error': 'Invalid data types for relay_id or state.'}), 400

    relay = Relay.query.get(relay_id) # Check if relay exists
    if not relay:
        return jsonify({'success': False, 'error': f'Relay with ID {relay_id} not found'}), 404
    
    relay_operation = {
        'id': relay_id,
        'state': state
    }
    if duration > 0 and state:
        relay_operation['duration'] = duration

    operations_list = [relay_operation]

    if publish_relay_control(operations_list):
        return jsonify({
            'success': True,
            'message': f'Relay {relay_id} command ({"ON" if state else "OFF"}) sent.'
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to send relay control command'}), 500

@api_bp.route('/relays/all-off', methods=['POST'])
def turn_all_relays_off():
    """
    Turn all relays off.
    """
    if not check_api_key(): # Assuming API key check is desired here too
        return jsonify({'success': False, 'error': 'Invalid API key'}), 401

    relays = Relay.query.all()
    if not relays:
        return jsonify({'success': True, 'message': 'No relays found to turn off.'}), 200 # Or 404 if preferred

    operations_list = []
    for relay in relays:
        operations_list.append({
            'id': relay.id,
            'state': False
            # No duration needed for 'off'
        })
    
    if operations_list:
        if publish_relay_control(operations_list):
            return jsonify({'success': True, 'message': f'{len(operations_list)} relays commanded OFF.'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send all-off command to relays.'}), 500
    else:
        return jsonify({'success': True, 'message': 'No relay operations to send.'}), 200 # Should not happen if relays exist

@api_bp.route('/relay-name', methods=['POST'])
def update_relay_name():
    """
    Update relay name
    """
    data = request.json
    
    if not data or 'relay_id' not in data or 'name' not in data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    relay_id = data.get('relay_id')
    name = data.get('name')
    
    # Find the relay
    relay = Relay.query.get(relay_id)
    if not relay:
        return jsonify({'success': False, 'error': f'Relay with ID {relay_id} not found'}), 404
    
    # Update name
    relay.name = name
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Relay {relay_id} name updated to {name}'
    })

@api_bp.route('/schedules', methods=['GET'])
def get_schedules():
    """
    Get all schedules
    """
    schedules = IrrigationSchedule.query.all()
    return jsonify({
        'success': True,
        'schedules': [s.to_dict() for s in schedules]
    })

@api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """
    Get a specific schedule
    """
    schedule = IrrigationSchedule.query.get_or_404(schedule_id)
    return jsonify({
        'success': True,
        'schedule': schedule.to_dict()
    })

@api_bp.route('/schedules', methods=['POST'])
def create_schedule():
    """
    Create a new schedule
    """
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    # Create a new schedule
    schedule = IrrigationSchedule(
        active=data.get('active', True),
        time=data.get('time', '00:00'),
        duration=data.get('duration', 0),
        priority=data.get('priority', 5)
    )
    
    # Set days and zones
    schedule.days_list = data.get('days', [])
    schedule.zones_list = data.get('zones', [])
    
    # Set sensor conditions if provided
    if 'sensor_condition' in data:
        schedule.sensor_condition_dict = data['sensor_condition']
    
    # Calculate next run time
    schedule.calculate_next_run()
    
    # Save to database
    db.session.add(schedule)
    db.session.commit()
    
    # Publish schedule to device
    publish_schedule(schedule)
    
    return jsonify({
        'success': True,
        'message': 'Schedule created successfully',
        'schedule': schedule.to_dict()
    }), 201

@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """
    Update an existing schedule
    """
    schedule = IrrigationSchedule.query.get_or_404(schedule_id)
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    # Update fields
    if 'active' in data:
        schedule.active = data['active']
    if 'time' in data:
        schedule.time = data['time']
    if 'duration' in data:
        schedule.duration = data['duration']
    if 'priority' in data:
        schedule.priority = data['priority']
    if 'days' in data:
        schedule.days_list = data['days']
    if 'zones' in data:
        schedule.zones_list = data['zones']
    if 'sensor_condition' in data:
        schedule.sensor_condition_dict = data['sensor_condition']
    
    # Calculate next run time
    schedule.calculate_next_run()
    
    # Save changes
    db.session.commit()
    
    # Publish updated schedule to device
    publish_schedule(schedule)
    
    return jsonify({
        'success': True,
        'message': 'Schedule updated successfully',
        'schedule': schedule.to_dict()
    })

@api_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule_route(schedule_id):
    """
    Delete a schedule
    """
    schedule = IrrigationSchedule.query.get_or_404(schedule_id)
    
    # Delete from the device first
    if delete_schedule(schedule_id):
        # Then delete from database
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Schedule {schedule_id} deleted'
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to delete schedule from device'}), 500

@api_bp.route('/environment', methods=['POST'])
def update_environment():
    """
    Update environmental conditions
    """
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    # Update local database
    SensorData.update_environmental_data(data)
    
    # Publish to device
    if publish_environment_update(data):
        return jsonify({
            'success': True,
            'message': 'Environment updated'
        })
    else:
        return jsonify({'success': False, 'error': 'Failed to update environment on device'}), 500

@api_bp.route('/settings', methods=['GET'])
def get_all_settings():
    """
    Get all application settings
    """
    settings = Settings.get_all()
    return jsonify({
        'success': True,
        'settings': settings
    })

@api_bp.route('/settings/<string:key>', methods=['GET'])
def get_setting(key):
    """
    Get a specific setting by key
    """
    value = Settings.get(key)
    if value is None:
        return jsonify({'success': False, 'error': f'Setting {key} not found'}), 404
    
    return jsonify({
        'success': True,
        'key': key,
        'value': value
    })

@api_bp.route('/settings', methods=['POST'])
def update_settings():
    """
    Update multiple settings at once
    """
    data = request.json
    
    if not data or not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400
    
    # Update each setting
    for key, value in data.items():
        Settings.set(key, value)
    
    return jsonify({
        'success': True,
        'message': 'Settings updated successfully'
    })

@api_bp.route('/settings/<string:key>', methods=['PUT'])
def update_setting(key):
    """
    Update a specific setting
    """
    data = request.json
    
    if 'value' not in data:
        return jsonify({'success': False, 'error': 'Missing value in request'}), 400
    
    Settings.set(key, data['value'])
    
    return jsonify({
        'success': True,
        'message': f'Setting {key} updated successfully'
    })

@api_bp.route('/settings/<string:key>', methods=['DELETE'])
def delete_setting(key):
    """
    Delete a setting
    """
    if Settings.delete(key):
        return jsonify({
            'success': True,
            'message': f'Setting {key} deleted successfully'
        })
    else:
        return jsonify({'success': False, 'error': f'Setting {key} not found'}), 404

@api_bp.route('/settings/system-status', methods=['GET'])
def system_status():
    """
    Get system status information
    """
    from app.routes.main import get_database_stats
    
    # Get database stats using the helper function
    stats = get_database_stats()
    
    return jsonify({
        'success': True,
        'db_size': stats['size'],
        'sensor_records': stats['sensor_records'],
        'mqtt_status': stats['mqtt_status']
    })

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    Get MQTT logs, paginated, with filtering and sorting.
    Query params: 
        page (int, default 1)
        per_page (int, default 20)
        level (str, e.g., INFO, WARNING - filters for this level and above)
        type (str, e.g., performance - filters for specific log_type)
        tag (str, filter by specific tag)
        message_contains (str, search text in message, case-insensitive)
        event_name (str, filter by performance event name)
        core_id (int, filter by core_id)
        sort_by (str, field to sort by, e.g., server_timestamp, level_num, duration_ms)
        sort_order (str, 'asc' or 'desc', default 'desc' for server_timestamp)
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filter_level_str = request.args.get('level', None, type=str)
    filter_log_type = request.args.get('type', None, type=str)
    filter_tag = request.args.get('tag', None, type=str)
    filter_message = request.args.get('message_contains', None, type=str)
    filter_event_name = request.args.get('event_name', None, type=str)
    filter_core_id = request.args.get('core_id', None, type=int)

    sort_by = request.args.get('sort_by', 'server_timestamp', type=str)
    sort_order = request.args.get('sort_order', 'desc', type=str)

    query = MqttLog.query

    log_level_map = {
        'DEBUG': 1, 'INFO': 2, 'WARNING': 3, 'ERROR': 4, 'CRITICAL': 5
    }

    if filter_level_str and filter_level_str.upper() in log_level_map:
        min_level_num = log_level_map[filter_level_str.upper()]
        query = query.filter(MqttLog.level_num >= min_level_num)
    
    if filter_log_type:
        query = query.filter(MqttLog.log_type == filter_log_type)
    
    if filter_tag:
        query = query.filter(MqttLog.tag.ilike(f'%{filter_tag}%')) # Case-insensitive like

    if filter_message:
        query = query.filter(MqttLog.message.ilike(f'%{filter_message}%')) # Case-insensitive like

    if filter_event_name:
        query = query.filter(MqttLog.event_name.ilike(f'%{filter_event_name}%')) # Case-insensitive like

    if filter_core_id is not None:
        query = query.filter(MqttLog.core_id == filter_core_id)

    # Sorting logic
    valid_sort_fields = {
        'server_timestamp': MqttLog.server_timestamp,
        'level_num': MqttLog.level_num,
        'tag': MqttLog.tag,
        'duration_ms': MqttLog.duration_ms, # Useful for performance logs
        'free_heap': MqttLog.free_heap
    }

    if sort_by in valid_sort_fields:
        sort_column = valid_sort_fields[sort_by]
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    else:
        # Default sort if sort_by is invalid or not specified for safety
        query = query.order_by(MqttLog.server_timestamp.desc())
    
    paginated_logs = query.paginate(page=page, per_page=per_page, error_out=False)
    logs_data = [log.to_dict() for log in paginated_logs.items]
    
    return jsonify({
        'success': True,
        'logs': logs_data,
        'total': paginated_logs.total,
        'pages': paginated_logs.pages,
        'current_page': paginated_logs.page,
        'has_next': paginated_logs.has_next,
        'has_prev': paginated_logs.has_prev
    })

@api_bp.route('/logconfig', methods=['POST'])
def post_log_config():
    """
    Send a log configuration command via MQTT.
    JSON Payload: {"target": "serial"|"mqtt", "level": "NONE"|"CRITICAL"|...|"DEBUG"}
    """
    data = request.json
    if not data or 'target' not in data or 'level' not in data:
        return jsonify({'success': False, 'error': 'Missing target or level in payload'}), 400

    target = data.get('target')
    level = data.get('level')
    
    # Basic validation for target and level values
    valid_targets = ['serial', 'mqtt']
    valid_levels = ['NONE', 'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
    if target not in valid_targets:
        return jsonify({'success': False, 'error': f'Invalid target: {target}. Must be one of {valid_targets}'}), 400
    if level not in valid_levels:
        return jsonify({'success': False, 'error': f'Invalid level: {level}. Must be one of {valid_levels}'}), 400

    if publish_log_config(target, level):
        return jsonify({'success': True, 'message': f'Log config command sent to target {target} with level {level}'})
    else:
        return jsonify({'success': False, 'error': 'Failed to send log config command'}), 500 

# --- Relay Preset API Endpoints ---
@api_bp.route('/presets', methods=['POST'])
def create_relay_preset():
    if not check_api_key(): return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    data = request.json
    if not data or not data.get('name') or not data.get('configuration'):
        return jsonify({'success': False, 'error': 'Missing name or configuration'}), 400
    if not isinstance(data.get('configuration'), list):
        return jsonify({'success': False, 'error': 'Configuration must be a list'}), 400

    existing_preset = RelayPreset.query.filter_by(name=data['name']).first()
    if existing_preset:
        return jsonify({'success': False, 'error': 'Preset name already exists'}), 409 # Conflict

    try:
        preset = RelayPreset(
            name=data['name'],
            description=data.get('description')
        )
        preset.set_configuration(data['configuration']) # This also validates the configuration list
        db.session.add(preset)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Preset created', 'preset': preset.to_dict()}), 201
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating preset: {e}")
        return jsonify({'success': False, 'error': 'Could not create preset'}), 500

@api_bp.route('/presets', methods=['GET'])
def get_all_relay_presets():
    if not check_api_key(): return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    presets = RelayPreset.query.order_by(RelayPreset.name).all()
    # Pass include_config=False if you don't want the full config in the list view
    return jsonify({'success': True, 'presets': [p.to_dict(include_config=False) for p in presets]})

@api_bp.route('/presets/<int:preset_id>', methods=['GET'])
def get_relay_preset(preset_id):
    if not check_api_key(): return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    preset = RelayPreset.query.get_or_404(preset_id)
    return jsonify({'success': True, 'preset': preset.to_dict()})

@api_bp.route('/presets/<int:preset_id>', methods=['PUT'])
def update_relay_preset(preset_id):
    if not check_api_key(): return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    preset = RelayPreset.query.get_or_404(preset_id)
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if 'name' in data:
        new_name = data['name']
        if new_name != preset.name and RelayPreset.query.filter_by(name=new_name).first():
            return jsonify({'success': False, 'error': 'Preset name already exists'}), 409
        preset.name = new_name
    if 'description' in data:
        preset.description = data['description']
    if 'configuration' in data:
        if not isinstance(data['configuration'], list):
            return jsonify({'success': False, 'error': 'Configuration must be a list'}), 400
        try:
            preset.set_configuration(data['configuration'])
        except ValueError as ve:
            return jsonify({'success': False, 'error': str(ve)}), 400

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Preset updated', 'preset': preset.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating preset {preset_id}: {e}")
        return jsonify({'success': False, 'error': 'Could not update preset'}), 500

@api_bp.route('/presets/<int:preset_id>', methods=['DELETE'])
def delete_relay_preset(preset_id):
    if not check_api_key(): return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    preset = RelayPreset.query.get_or_404(preset_id)
    try:
        db.session.delete(preset)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Preset deleted'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting preset {preset_id}: {e}")
        return jsonify({'success': False, 'error': 'Could not delete preset'}), 500

@api_bp.route('/presets/<int:preset_id>/apply', methods=['POST'])
def apply_relay_preset(preset_id):
    if not check_api_key(): return jsonify({'success': False, 'error': 'Invalid API key'}), 401
    preset = RelayPreset.query.get_or_404(preset_id)
    
    operations = preset.get_configuration()
    if not operations:
        return jsonify({'success': False, 'error': 'Preset has no operations configured or configuration is invalid.'}), 400

    if publish_relay_control(operations):
        return jsonify({'success': True, 'message': f'Preset "{preset.name}" applied successfully.'})
    else:
        return jsonify({'success': False, 'error': f'Failed to apply preset "{preset.name}".'}), 500 