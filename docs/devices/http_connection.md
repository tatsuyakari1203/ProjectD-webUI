# HTTP Connection Instructions

## HTTP API Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Endpoint URL | /api/publish | Base endpoint for sending data |
| Method | POST | HTTP method for sending data |
| Content-Type | application/json | Required header |
| Authentication | API Key | Include in HTTP header |

## Connection Process

### 1. Prepare Your Request

Create an HTTP POST request to the endpoint `/api/publish` with appropriate headers:

```
Content-Type: application/json
```

### 2. Include API Key in Request

Include your API key in the request header:

* Request headers: `X-API-Key: YOUR_API_KEY`

### 3. Format Your JSON Payload

Include the necessary data fields in your JSON payload:

```json
{
  "device": "my_device",
  "topic": "temperature",
  "payload": {
    "temperature": 25.5,
    "humidity": 45.2,
    "timestamp": "2025-03-23T07:30:00",
    "unit": "celsius"
  }
}
```

## Example Arduino/ESP8266 Code

```cpp
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>

// WiFi settings
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// API and device settings
const char* server_url = "http://YOUR_SERVER_IP/api/publish";
const char* api_key = "YOUR_API_KEY"; // Your API key from the clients page
const char* device_name = "esp8266_1";
const char* topic_name = "temperature";

void setup() {
  Serial.begin(115200);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    
    // Start connection
    http.begin(client, server_url);
    http.addHeader("Content-Type", "application/json");
    
    // API key must be sent in header
    http.addHeader("X-API-Key", api_key);
    
    // Read sensor data
    float temp = 25.5; // Replace with actual sensor reading
    float humidity = 45.2; // Replace with actual sensor reading
    String timestamp = "2025-03-23T07:30:00"; // Use current timestamp
    
    // Create JSON payload according to API requirements
    StaticJsonDocument<256> doc;
    doc["device"] = device_name;
    doc["topic"] = topic_name;
    
    JsonObject payload = doc.createNestedObject("payload");
    payload["temperature"] = temp;
    payload["humidity"] = humidity;
    payload["timestamp"] = timestamp;
    payload["unit"] = "celsius";
    
    String requestBody;
    serializeJson(doc, requestBody);
    
    Serial.print("Sending HTTP POST: ");
    Serial.println(requestBody);
    
    // Send the POST request
    int httpResponseCode = http.POST(requestBody);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP Response code: " + String(httpResponseCode));
      Serial.println("Response: " + response);
    } else {
      Serial.print("Error on sending POST: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
  
  delay(30000); // Send data every 30 seconds
}
