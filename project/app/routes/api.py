from flask import Blueprint, jsonify, request, current_app
from app.models.relay import Relay
from app.models.sensor import SensorData
from app.models.schedule import IrrigationSchedule
from app.services.mqtt_service import publish_relay_control, publish_schedule, delete_schedule, publish_environment_update
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
        return jsonify({'error': 'Unauthorized'}), 401

@api_bp.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    """
    Get latest sensor data
    """
    # Get latest sensor data
    sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    if not sensor:
        return jsonify({'error': 'No sensor data available'}), 404
    
    return jsonify(sensor.to_dict())

@api_bp.route('/sensor-data/history', methods=['GET'])
def get_sensor_history():
    """
    Get sensor data history
    """
    # Get time range from query parameters
    hours = request.args.get('hours', default=24, type=int)
    
    # Calculate start time
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get sensor data in time range
    sensors = SensorData.query.filter(
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp).all()
    
    return jsonify([s.to_dict() for s in sensors])

@api_bp.route('/relay-status', methods=['GET'])
def get_relay_status():
    """
    Get status of all relays
    """
    relays = Relay.query.all()
    return jsonify([r.to_dict() for r in relays])

@api_bp.route('/relay-control', methods=['POST'])
def relay_control():
    """
    Control relay state
    """
    data = request.json
    
    if not data or 'relay_id' not in data or 'state' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    relay_id = data.get('relay_id')
    state = data.get('state')
    duration = data.get('duration', 0)
    
    # Find the relay
    relay = Relay.query.get(relay_id)
    if not relay:
        return jsonify({'error': f'Relay with ID {relay_id} not found'}), 404
    
    # Publish relay control command
    if publish_relay_control(relay_id, state, duration):
        return jsonify({'message': f'Relay {relay_id} {"turned ON" if state else "turned OFF"}'})
    else:
        return jsonify({'error': 'Failed to control relay'}), 500

@api_bp.route('/relay-name', methods=['POST'])
def update_relay_name():
    """
    Update relay name
    """
    data = request.json
    
    if not data or 'relay_id' not in data or 'name' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    relay_id = data.get('relay_id')
    name = data.get('name')
    
    # Find the relay
    relay = Relay.query.get(relay_id)
    if not relay:
        return jsonify({'error': f'Relay with ID {relay_id} not found'}), 404
    
    # Update name
    relay.name = name
    db.session.commit()
    
    return jsonify({'message': f'Relay {relay_id} name updated to {name}'})

@api_bp.route('/schedules', methods=['GET'])
def get_schedules():
    """
    Get all schedules
    """
    schedules = IrrigationSchedule.query.all()
    return jsonify([s.to_dict() for s in schedules])

@api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """
    Get a specific schedule
    """
    schedule = IrrigationSchedule.query.get_or_404(schedule_id)
    return jsonify(schedule.to_dict())

@api_bp.route('/schedules', methods=['POST'])
def create_schedule():
    """
    Create a new schedule
    """
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
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
    
    return jsonify(schedule.to_dict()), 201

@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """
    Update an existing schedule
    """
    schedule = IrrigationSchedule.query.get_or_404(schedule_id)
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
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
    
    return jsonify(schedule.to_dict())

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
        return jsonify({'message': f'Schedule {schedule_id} deleted'})
    else:
        return jsonify({'error': 'Failed to delete schedule from device'}), 500

@api_bp.route('/environment', methods=['POST'])
def update_environment():
    """
    Update environmental conditions
    """
    data = request.json
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    # Update local database
    SensorData.update_environmental_data(data)
    
    # Publish to device
    if publish_environment_update(data):
        return jsonify({'message': 'Environment updated'})
    else:
        return jsonify({'error': 'Failed to update environment on device'}), 500 