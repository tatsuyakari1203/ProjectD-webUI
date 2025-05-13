from datetime import datetime
import json
from app import db

class SensorData(db.Model):
    """
    SensorData model - stores environmental sensor readings
    """
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    temperature = db.Column(db.Float)  # Temperature in Celsius
    humidity = db.Column(db.Float)     # Air humidity in %
    heat_index = db.Column(db.Float)   # Heat index in Celsius
    soil_moisture = db.Column(db.String(256))  # JSON string for zone-based soil moisture
    rain = db.Column(db.Boolean, default=False)  # Rain status
    light = db.Column(db.Integer)      # Light level in lux
    
    def __repr__(self):
        return f'<SensorData id={self.id} temp={self.temperature}°C hum={self.humidity}%>'
    
    def to_dict(self):
        """
        Convert sensor data object to dictionary
        """
        soil_moisture_data = {}
        if self.soil_moisture:
            try:
                soil_moisture_data = json.loads(self.soil_moisture)
            except json.JSONDecodeError:
                soil_moisture_data = {}
                
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'heat_index': self.heat_index,
            'soil_moisture': soil_moisture_data,
            'rain': self.rain,
            'light': self.light
        }
    
    @staticmethod
    def from_mqtt_data(data):
        """
        Create sensor data object from MQTT data
        """
        if not data:
            return None
            
        # Create a new SensorData record
        sensor_data = SensorData(
            temperature=data.get('temperature'),
            humidity=data.get('humidity'),
            heat_index=data.get('heat_index')
        )
        
        # Handle timestamp if provided
        if 'timestamp' in data:
            try:
                sensor_data.timestamp = datetime.fromtimestamp(data['timestamp'])
            except (ValueError, TypeError):
                sensor_data.timestamp = datetime.utcnow()
        
        db.session.add(sensor_data)
        db.session.commit()
        
        return sensor_data
    
    @staticmethod
    def update_environmental_data(data):
        """
        Update environmental data (soil_moisture, rain, light)
        """
        if not data:
            return None
            
        # Get the latest sensor data record
        sensor_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        
        if not sensor_data:
            # Create a new record if none exists
            sensor_data = SensorData(timestamp=datetime.utcnow())
            db.session.add(sensor_data)
        
        # Update soil moisture if provided
        if 'soil_moisture' in data:
            soil_moisture_data = {}
            if sensor_data.soil_moisture:
                try:
                    soil_moisture_data = json.loads(sensor_data.soil_moisture)
                except json.JSONDecodeError:
                    soil_moisture_data = {}
            
            # Add/update the zone data
            zone = data['soil_moisture'].get('zone')
            value = data['soil_moisture'].get('value')
            if zone and value is not None:
                soil_moisture_data[str(zone)] = value
                sensor_data.soil_moisture = json.dumps(soil_moisture_data)
        
        # Update rain status if provided
        if 'rain' in data:
            sensor_data.rain = bool(data['rain'])
        
        # Update light level if provided
        if 'light' in data:
            sensor_data.light = data['light']
        
        db.session.commit()
        return sensor_data 