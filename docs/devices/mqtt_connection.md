# MQTT Connection Instructions

## MQTT Broker Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Broker Host | Server IP/hostname | Your server address |
| Broker Port | 1883 | Default MQTT port |
| Broker Username | admin | Default Mosquitto configuration |
| Broker Password | admin | Default Mosquitto configuration |
| Topic Format | device_name/topic_name | Example: esp8266_1/temperature |
| API Key | Required | Must be included in every JSON payload |

## Connection Process

### 1. Connect to MQTT Broker

Connect to the broker using its host, port, and authentication credentials:

```
username: admin
password: admin
```

### 2. Format Your Topic

Create a topic using the format `device_name/topic_name`, for example `esp8266_1/temperature`.

### 3. Include API Key in Payload

Add your API key to the JSON payload to authenticate your device:

```json
{
  "api_key": "YOUR_API_KEY", 
  "temperature": 25.5,
  "humidity": 45.2,
  "timestamp": "2025-03-23T07:30:00",
  "unit": "celsius"
}
```

The API key is used for authentication, and all other fields will be stored as your data payload.

### 4. Publish Messages

Send your data to the topic and the server will process it automatically.

## Example Arduino/ESP8266 Code

```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi settings
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT broker settings
const char* mqtt_server = "YOUR_SERVER_IP"; // Your server IP
const int mqtt_port = 1883;
const char* mqtt_username = "admin";
const char* mqtt_password = "admin";

// API and device settings
const char* api_key = "YOUR_API_KEY"; // Your API key from the clients page
const char* device_name = "esp8266_1";
const char* topic_name = "temperature";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  
  // Connect to MQTT
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Read sensor data
  float temp = 25.5; // Replace with actual sensor reading
  float humidity = 45.2; // Replace with actual sensor reading
  
  // Create full topic (device_name/topic_name)
  String topic = String(device_name) + "/" + String(topic_name);
  
  // Create JSON payload WITH API key
  StaticJsonDocument<200> doc;
  doc["api_key"] = api_key; // API key must be included in every message
  doc["temperature"] = temp;
  doc["humidity"] = humidity;
  doc["timestamp"] = millis();
  doc["unit"] = "celsius";
  
  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  
  // Publish to MQTT
  Serial.print("Publishing to topic: ");
  Serial.println(topic);
  Serial.print("Payload: ");
  Serial.println(jsonBuffer);
  
  client.publish(topic.c_str(), jsonBuffer);
  delay(5000);
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    
    // Attempt to connect with username/password
    if (client.connect(clientId.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
