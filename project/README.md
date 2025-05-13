# Irrigation Control System Web Application

A modern web application for monitoring and controlling an ESP32-S3 6-Relay irrigation system. Built with Flask, SQLAlchemy, Bootstrap 5, and MQTT.

## Features

- **Modern Dark Mode UI**: Clean, responsive interface with Bootstrap 5
- **Real-time Monitoring**: Track sensor data and relay states
- **Irrigation Scheduling**: Create and manage irrigation schedules
- **Environmental Conditions**: Monitor temperature, humidity, and more
- **Sensor-based Rules**: Set up irrigation based on environmental conditions

## Technical Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Chart.js
- **Communication**: MQTT for device control, HTTP for data retrieval

## Installation

1. Clone the repository:
```
git clone <repository-url>
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install requirements:
```
pip install -r requirements.txt
```

4. Set up environment variables (optional):
```
export SECRET_KEY=your-secret-key
export MQTT_BROKER_URL=your-mqtt-broker
export API_KEY=your-api-key
```

5. Initialize the database:
```
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Run the application:
```
flask run
```

## Configuration

Configuration options are in `config.py`. You can override these with environment variables:

- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: SQLite database URL
- `MQTT_BROKER_URL`: MQTT broker address
- `MQTT_BROKER_PORT`: MQTT broker port
- `MQTT_CLIENT_ID`: MQTT client ID
- `API_KEY`: API key for authentication

## Project Structure

```
project_root/
├── app/
│   ├── __init__.py             # Flask app initialization
│   ├── models/                 # SQLAlchemy models
│   ├── services/               # Business logic
│   ├── routes/                 # Flask Blueprints
│   ├── static/                 # Static assets
│   └── templates/              # Jinja2 templates
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── migrations/                 # Database migrations
└── run.py                      # Application entry point
```

## MQTT Topics

The application communicates with the irrigation device using these MQTT topics:

- `irrigation/esp32_6relay/sensors`: Receiving sensor data
- `irrigation/esp32_6relay/status`: Receiving relay status
- `irrigation/esp32_6relay/schedule/status`: Receiving schedule status
- `irrigation/esp32_6relay/control`: Sending relay control commands
- `irrigation/esp32_6relay/schedule`: Sending schedule commands
- `irrigation/esp32_6relay/environment`: Sending environment updates

## API Endpoints

The application provides REST API endpoints:

- `/api/sensor-data`: Get latest sensor data
- `/api/relay-status`: Get relay status
- `/api/relay-control`: Control relay state
- `/api/schedules`: Manage schedules
- `/api/environment`: Update environmental conditions

## License

This project is licensed under the MIT License - see the LICENSE file for details. 