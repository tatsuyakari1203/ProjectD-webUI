import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy with no settings
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=None):
    """
    Create and configure the Flask application
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Load configuration
    if config_class is None:
        # Use Config from config.py by default
        from config import Config
        app.config.from_object(Config)
    else:
        # Use provided config class if available
        app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize MQTT service
    from app.services.mqtt_service import init_mqtt
    with app.app_context():
        init_mqtt(app)
    
    return app

from app.models import relay, schedule, sensor 