# Ví dụ (Arduino/ESP8266)

Ví dụ code ESP8266 sử dụng HTTP API để gửi dữ liệu:

```cpp
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* server_url = "http://{{ server_host }}/api/publish";
const char* api_key = "YOUR_API_KEY";
const char* device_name = "esp8266_sensor";
const char* topic_name = "temperature";

void setup() {
  Serial.begin(115200);
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(server_url);
    
    // Add API key to headers
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", api_key);
    
    // Create JSON payload
    StaticJsonDocument<200> doc;
    doc["device"] = device_name;
    doc["topic"] = topic_name;
    
    JsonObject payload = doc.createNestedObject("payload");
    payload["value"] = 25.5; // Replace with actual sensor reading
    payload["unit"] = "celsius";
    payload["timestamp"] = millis();
    
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    // Send POST request
    Serial.print("Sending HTTP POST: ");
    Serial.println(jsonPayload);
    
    int httpCode = http.POST(jsonPayload);
    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("Response code: " + String(httpCode));
      Serial.println("Response: " + response);
    } else {
      Serial.println("HTTP request failed");
    }
    
    http.end();
    delay(5000);
  }
}
```
