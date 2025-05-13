from datetime import datetime, timedelta
import json
from app import db

class IrrigationSchedule(db.Model):
    """
    IrrigationSchedule model - represents a scheduled irrigation task
    """
    __tablename__ = 'irrigation_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True)
    days = db.Column(db.String(64))  # JSON array of days (1-7)
    time = db.Column(db.String(5))   # Time in HH:MM format
    duration = db.Column(db.Integer)  # Duration in minutes
    zones = db.Column(db.String(64))  # JSON array of zone IDs
    priority = db.Column(db.Integer, default=5)  # Priority 1-10
    state = db.Column(db.String(16), default='idle')  # idle, running, completed
    next_run = db.Column(db.DateTime)  # Next scheduled run time
    sensor_condition = db.Column(db.Text)  # JSON sensor conditions
    
    def __repr__(self):
        return f'<Schedule {self.id}: {self.time} for {self.duration}min zones={self.zones_list}>'
    
    @property
    def days_list(self):
        """Get days as a list of integers"""
        if not self.days:
            return []
        try:
            return json.loads(self.days)
        except json.JSONDecodeError:
            return []
    
    @days_list.setter
    def days_list(self, value):
        """Set days from a list of integers"""
        if isinstance(value, list):
            self.days = json.dumps(value)
    
    @property
    def zones_list(self):
        """Get zones as a list of integers"""
        if not self.zones:
            return []
        try:
            return json.loads(self.zones)
        except json.JSONDecodeError:
            return []
    
    @zones_list.setter
    def zones_list(self, value):
        """Set zones from a list of integers"""
        if isinstance(value, list):
            self.zones = json.dumps(value)
    
    @property
    def sensor_condition_dict(self):
        """Get sensor condition as a dictionary"""
        if not self.sensor_condition:
            return {}
        try:
            return json.loads(self.sensor_condition)
        except json.JSONDecodeError:
            return {}
    
    @sensor_condition_dict.setter
    def sensor_condition_dict(self, value):
        """Set sensor condition from a dictionary"""
        if isinstance(value, dict):
            self.sensor_condition = json.dumps(value)
    
    def to_dict(self):
        """
        Convert schedule object to dictionary
        """
        return {
            'id': self.id,
            'active': self.active,
            'days': self.days_list,
            'time': self.time,
            'duration': self.duration,
            'zones': self.zones_list,
            'priority': self.priority,
            'state': self.state,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'sensor_condition': self.sensor_condition_dict
        }
    
    def calculate_next_run(self):
        """
        Calculate the next run time based on the schedule
        """
        if not self.active or not self.days_list or not self.time:
            self.next_run = None
            return
        
        now = datetime.utcnow()
        days_ahead = []
        
        # Parse the time
        try:
            hour, minute = map(int, self.time.split(':'))
        except (ValueError, AttributeError):
            self.next_run = None
            return
        
        # Get the current day of week (1-7, where 1 is Monday)
        current_weekday = now.weekday() + 1  # Convert from 0-6 to 1-7
        
        # Find days ahead
        for day in self.days_list:
            day_diff = (day - current_weekday) % 7
            if day_diff == 0:
                # Same day - check if time is in the future
                schedule_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if schedule_time > now:
                    days_ahead.append(0)
                else:
                    days_ahead.append(7)  # Next week
            else:
                days_ahead.append(day_diff)
        
        if not days_ahead:
            self.next_run = None
            return
        
        # Get the closest next run
        next_day = min(days_ahead)
        next_date = now + timedelta(days=next_day)
        self.next_run = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    @staticmethod
    def from_mqtt_data(data):
        """
        Create or update schedule objects from MQTT data
        """
        schedules = []
        if not data or 'tasks' not in data:
            return schedules
            
        for task_data in data['tasks']:
            task_id = task_data.get('id')
            if not task_id:
                continue
                
            schedule = IrrigationSchedule.query.get(task_id)
            if not schedule:
                schedule = IrrigationSchedule(id=task_id)
                db.session.add(schedule)
                
            schedule.active = task_data.get('active', True)
            schedule.days_list = task_data.get('days', [])
            schedule.time = task_data.get('time', '00:00')
            schedule.duration = task_data.get('duration', 0)
            schedule.zones_list = task_data.get('zones', [])
            schedule.priority = task_data.get('priority', 5)
            
            if 'state' in task_data:
                schedule.state = task_data['state']
            
            if 'sensor_condition' in task_data:
                schedule.sensor_condition_dict = task_data['sensor_condition']
            
            # Calculate next run time
            schedule.calculate_next_run()
            
            # If next_run is provided explicitly, use it
            if 'next_run' in task_data and task_data['next_run']:
                try:
                    schedule.next_run = datetime.fromisoformat(task_data['next_run'].replace(' ', 'T'))
                except (ValueError, TypeError):
                    pass
            
            schedules.append(schedule)
            
        db.session.commit()
        return schedules 