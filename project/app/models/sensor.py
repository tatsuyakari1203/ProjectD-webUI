from datetime import datetime
import json
from app import db
from flask import current_app # Added for logging if needed

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
    
    # New fields for primary soil moisture sensor
    primary_soil_moisture_value = db.Column(db.Float) 
    primary_soil_moisture_unit = db.Column(db.String(32))

    # Existing field, role to be clarified (potentially for zoned data if still used)
    soil_moisture_zones_json = db.Column(db.String(256), name='soil_moisture')  # JSON string for zone-based soil moisture, renamed attribute for clarity
    
    rain = db.Column(db.Boolean, default=False)  # Rain status
    light = db.Column(db.Integer)      # Light level in lux
    
    # To store the raw device_info if needed by API, e.g. for type/firmware display
    device_info_json = db.Column(db.String(256))

    def __repr__(self):
        return f'<SensorData id={self.id} temp={self.temperature}°C hum={self.humidity}% psm={self.primary_soil_moisture_value}{self.primary_soil_moisture_unit or ""}>'
    
    def to_dict(self):
        """
        Convert sensor data object to dictionary
        """
        soil_moisture_zones_data = {}
        if self.soil_moisture_zones_json:
            try:
                soil_moisture_zones_data = json.loads(self.soil_moisture_zones_json)
            except json.JSONDecodeError:
                soil_moisture_zones_data = {}
        
        device_info_data = None
        if self.device_info_json:
            try:
                device_info_data = json.loads(self.device_info_json)
            except json.JSONDecodeError:
                device_info_data = None

        # Transform unit for display
        display_psm_unit = self.primary_soil_moisture_unit
        if self.primary_soil_moisture_unit and self.primary_soil_moisture_unit.lower() == 'percent':
            display_psm_unit = '%'

        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'heat_index': self.heat_index,
            'primary_soil_moisture_value': self.primary_soil_moisture_value,
            'primary_soil_moisture_unit': display_psm_unit, # Use the transformed unit
            'soil_moisture': soil_moisture_zones_data, 
            'rain': self.rain,
            'light': self.light,
            'device_info': device_info_data
        }
    
    @staticmethod
    def from_mqtt_data(data):
        """
        Create sensor data object from MQTT data
        """
        if not data:
            return None
        
        def _get_nested_value(payload, key, sub_key='value'):
            field_data = payload.get(key)
            if isinstance(field_data, dict):
                return field_data.get(sub_key)
            return field_data # Assumes it might be a direct value if not a dict

        temp_val = _get_nested_value(data, 'temperature')
        hum_val = _get_nested_value(data, 'humidity')
        hi_val = _get_nested_value(data, 'heat_index')
        
        # Primary Soil Moisture
        psm_val = None
        psm_unit = None
        soil_moisture_payload = data.get('soil_moisture')
        if isinstance(soil_moisture_payload, dict):
            psm_val = soil_moisture_payload.get('value')
            psm_unit = soil_moisture_payload.get('unit')

        # Light
        light_val = _get_nested_value(data, 'light')
        
        # Rain (assuming it's a direct boolean in the payload as per ESP32 example)
        rain_val = data.get('rain', False) # Default to False if not present

        # Device Info
        device_info_payload = data.get('device_info')
        device_info_str = json.dumps(device_info_payload) if isinstance(device_info_payload, dict) else None

        sensor_data = SensorData(
            temperature=float(temp_val) if temp_val is not None else None,
            humidity=float(hum_val) if hum_val is not None else None,
            heat_index=float(hi_val) if hi_val is not None else None,
            primary_soil_moisture_value=float(psm_val) if psm_val is not None else None,
            primary_soil_moisture_unit=psm_unit,
            light=int(light_val) if light_val is not None else None,
            rain=bool(rain_val),
            device_info_json=device_info_str
            # soil_moisture_zones_json is NOT populated here from primary sensor data
        )
        
        if 'timestamp' in data:
            try:
                ts_data = data['timestamp']
                if isinstance(ts_data, (int, float)):
                    sensor_data.timestamp = datetime.fromtimestamp(ts_data)
                # Handle ISO format string if that's what ESP32 sends
                elif isinstance(ts_data, str):
                    sensor_data.timestamp = datetime.fromisoformat(ts_data.replace('Z', '+00:00'))
                else:
                    sensor_data.timestamp = datetime.utcnow()
            except (ValueError, TypeError) as e:
                # current_app.logger.error(f"Error parsing timestamp {data['timestamp']}: {e}")
                sensor_data.timestamp = datetime.utcnow()
        else:
            sensor_data.timestamp = datetime.utcnow()
        
        # For debugging what's about to be saved:
        # print(f"Saving sensor data: temp={sensor_data.temperature}, hum={sensor_data.humidity}, psm_val={sensor_data.primary_soil_moisture_value}, psm_unit={sensor_data.primary_soil_moisture_unit}, light={sensor_data.light}, rain={sensor_data.rain}")
        
        try:
            db.session.add(sensor_data)
            db.session.commit()
        except Exception as e:
            # current_app.logger.error(f"DB Error saving sensor data: {e}")
            db.session.rollback()
            return None # Or raise
        
        return sensor_data
    
    @staticmethod
    def update_environmental_data(data):
        """
        Update environmental data (typically for zoned soil_moisture, rain, light if updated manually/separately)
        This method might need review if primary sensor feed is the sole source.
        """
        if not data:
            return None
            
        sensor_data = SensorData.query.order_by(SensorData.timestamp.desc()).first()
        
        if not sensor_data:
            # current_app.logger.info("No existing sensor data found, creating new for env update.")
            sensor_data = SensorData(timestamp=datetime.utcnow())
            db.session.add(sensor_data)
        
        # This section is primarily for ZONED soil moisture if updated via this method
        if 'soil_moisture' in data: # Assuming 'soil_moisture' key here refers to ZONED data structure
            current_zones_data = {}
            if sensor_data.soil_moisture_zones_json:
                try:
                    current_zones_data = json.loads(sensor_data.soil_moisture_zones_json)
                except json.JSONDecodeError:
                    current_zones_data = {}
            
            new_zone_info = data['soil_moisture'] # e.g., {"zone": 1, "value": 25}
            if isinstance(new_zone_info, dict):
                zone = new_zone_info.get('zone')
                value = new_zone_info.get('value')
                if zone and value is not None:
                    current_zones_data[str(zone)] = value
                    sensor_data.soil_moisture_zones_json = json.dumps(current_zones_data)
            
        if 'rain' in data: # Manual override for rain
            rain_value = data['rain']
            if isinstance(rain_value, dict): rain_value = rain_value.get('value', sensor_data.rain)
            sensor_data.rain = bool(rain_value)
        
        if 'light' in data: # Manual override for light
            light_value = data['light']
            if isinstance(light_value, dict): light_value = light_value.get('value')
            sensor_data.light = int(light_value) if light_value is not None else sensor_data.light
        
        try:
            db.session.commit()
        except Exception as e:
            # current_app.logger.error(f"DB Error in update_environmental_data: {e}")
            db.session.rollback()
            return None
        return sensor_data 