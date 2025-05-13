from datetime import datetime
from app import db

class Relay(db.Model):
    """
    Relay model - represents a physical relay/zone in the irrigation system
    """
    __tablename__ = 'relays'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), default='Zone')
    state = db.Column(db.Boolean, default=False)
    remaining_time = db.Column(db.Integer, default=0)  # Remaining time in seconds
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Relay {self.id} - {self.name}: {"ON" if self.state else "OFF"}>'
    
    def to_dict(self):
        """
        Convert relay object to dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'remaining_time': self.remaining_time,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @staticmethod
    def from_mqtt_data(data):
        """
        Create or update relay objects from MQTT data
        """
        relays = []
        if not data or 'relays' not in data:
            return relays
            
        for relay_data in data['relays']:
            relay_id = relay_data.get('id')
            if not relay_id:
                continue
                
            relay = Relay.query.get(relay_id)
            if not relay:
                relay = Relay(id=relay_id, name=f'Zone {relay_id}')
                db.session.add(relay)
                
            relay.state = relay_data.get('state', False)
            relay.remaining_time = relay_data.get('remaining_time', 0)
            relay.last_updated = datetime.utcnow()
            relays.append(relay)
            
        db.session.commit()
        return relays 