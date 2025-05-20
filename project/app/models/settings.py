import json
from app import db

class Settings(db.Model):
    """
    Settings model - stores application settings
    """
    __tablename__ = 'settings'
    
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Setting {self.key}>'
    
    @staticmethod
    def get(key, default=None):
        """
        Get a setting value by key
        """
        setting = Settings.query.get(key)
        if setting and setting.value:
            try:
                return json.loads(setting.value)
            except json.JSONDecodeError:
                return setting.value
        return default
    
    @staticmethod
    def set(key, value):
        """
        Set a setting value
        """
        setting = Settings.query.get(key)
        if not setting:
            setting = Settings(key=key)
            db.session.add(setting)
        
        # Serialize complex objects to JSON
        if isinstance(value, (dict, list)):
            setting.value = json.dumps(value)
        else:
            setting.value = str(value)
        
        db.session.commit()
        return setting
    
    @staticmethod
    def delete(key):
        """
        Delete a setting
        """
        setting = Settings.query.get(key)
        if setting:
            db.session.delete(setting)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_all():
        """
        Get all settings as a dictionary
        """
        settings = Settings.query.all()
        result = {}
        
        for setting in settings:
            try:
                result[setting.key] = json.loads(setting.value)
            except (json.JSONDecodeError, TypeError):
                result[setting.key] = setting.value
        
        return result 