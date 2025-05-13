# Ví dụ (Arduino/ESP8266)

Ví dụ code ESP8266 sử dụng PubSubClient để kết nối với MQTT broker:

```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "{{ server_host }}";
const int mqtt_port = 1883;
const char* mqtt_username = "admin";
const char* mqtt_password = "admin";
const char* api_key = "YOUR_API_KEY";
const char* device_name = "esp8266_sensor";
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
  
  // Create full topic (device_name/topic_name)
  String topic = String(device_name) + "/" + String(topic_name);
  
  // Create JSON payload WITH API key
  StaticJsonDocument<200> doc;
  doc["api_key"] = api_key;
  doc["value"] = temp;
  doc["unit"] = "celsius";
  doc["timestamp"] = millis();
  
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
```
