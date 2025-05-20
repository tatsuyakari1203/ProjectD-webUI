import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sqlite3
import pathlib

# Initialize SQLAlchemy with no settings
db = SQLAlchemy()
migrate = Migrate()

# Ensure models are imported so SQLAlchemy and Alembic can see them.
# This needs to happen before Alembic tries to generate migrations based on db.metadata.
# Importing the models package or specific modules here is crucial.
from app import models # This will trigger app/models/__init__.py

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
    
    # Auto-setup database if it doesn't exist
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Handle sqlite URL format
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            
            # If relative path, make it relative to instance folder
            if not db_path.startswith('/'):
                db_path = os.path.join(app.instance_path, db_path)
            
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create empty database file if it doesn't exist
            if not os.path.exists(db_path):
                print(f"Database not found. Creating new database at {db_path}")
                # Create empty file
                try:
                    # Create a connection to create the file
                    conn = sqlite3.connect(db_path)
                    conn.close()
                    print(f"Empty database file created at {db_path}")
                except Exception as e:
                    print(f"Error creating database file: {e}")
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # It's generally better to let migrations handle table creation (db.upgrade)
    # than to use db.create_all() if you are using migrations.
    # However, for initial setup or if you want to ensure tables for non-migrated models:
    # with app.app_context():
    #     try:
    #         db.create_all() 
    #         print("Database tables (re)checked/created successfully via create_all().")
    #     except Exception as e:
    #         print(f"Error with db.create_all(): {e}")
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize MQTT service - đặt trong app context
    with app.app_context():
        from app.services.mqtt_service import init_mqtt
        init_mqtt(app)
    
    # Register custom Jinja2 filters
    @app.template_filter('zfill')
    def zfill_filter(value, width):
        return str(value).zfill(width)

    return app

# The specific model imports at the end of the file can be removed 
# if 'from app import models' at the top works as expected.
# from app.models import relay, schedule, sensor, settings, log, preset 