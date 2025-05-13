from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from app.models.relay import Relay
from app.models.sensor import SensorData
from app.models.schedule import IrrigationSchedule
from app.services.mqtt_service import publish_relay_control
from app import db

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
    duration = request.form.get('duration', type=int, default=0)
    
    if not relay_id or not action:
        flash('Invalid request', 'danger')
        return redirect(url_for('main.relays'))
    
    relay = Relay.query.get_or_404(relay_id)
    
    # Determine the state based on action
    if action == 'on':
        state = True
    elif action == 'off':
        state = False
    else:
        flash('Invalid action', 'danger')
        return redirect(url_for('main.relays'))
    
    # Publish relay control command
    if publish_relay_control(relay_id, state, duration):
        flash(f'Relay {relay_id} {"turned ON" if state else "turned OFF"}', 'success')
    else:
        flash('Failed to control relay', 'danger')
    
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
    # Get latest sensor data for display
    latest_sensor = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    
    # Get data for charts (last 24 hours)
    from datetime import datetime, timedelta
    start_time = datetime.utcnow() - timedelta(hours=24)
    
    sensor_history = SensorData.query.filter(
        SensorData.timestamp >= start_time
    ).order_by(SensorData.timestamp).all()
    
    return render_template(
        'sensors.html', 
        latest_sensor=latest_sensor,
        sensor_history=sensor_history,
        title='Sensor Data'
    )

@main_bp.route('/settings')
def settings():
    """
    Settings page
    """
    return render_template('settings.html', title='Settings') 