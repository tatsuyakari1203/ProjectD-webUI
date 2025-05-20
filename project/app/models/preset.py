from app import db
from datetime import datetime
import json

class RelayPreset(db.Model):
    __tablename__ = 'relay_presets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    # Configuration will store a JSON string of relay operations
    # e.g., '[{\"id\": 1, \"state\": true, \"duration\": 60}, {\"id\": 2, \"state\": false}]'
    # Duration here is in SECONDS as per user input, conversion to MS happens in mqtt_service
    configuration = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<RelayPreset {self.id} - {self.name}>'

    def to_dict(self, include_config=True):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_config:
            try:
                data['configuration'] = json.loads(self.configuration)
            except (json.JSONDecodeError, TypeError):
                data['configuration'] = [] # Or handle error appropriately
        return data

    def set_configuration(self, config_list):
        """Expects a list of operation dicts, stores as JSON string."""
        if not isinstance(config_list, list):
            raise ValueError("Configuration must be a list of operations.")
        # Basic validation for each operation in the list could be added here
        for op in config_list:
            if not all(k in op for k in ('id', 'state')):
                raise ValueError("Each operation must contain 'id' and 'state'.")
            if 'duration' in op and (not isinstance(op['duration'], int) or op['duration'] < 0):
                raise ValueError("Duration must be a non-negative integer (seconds).")

        self.configuration = json.dumps(config_list)

    def get_configuration(self):
        """Returns the configuration as a Python list of dicts."""
        try:
            return json.loads(self.configuration)
        except (json.JSONDecodeError, TypeError):
            return [] 