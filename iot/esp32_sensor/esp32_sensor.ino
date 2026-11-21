// Kissan AI - ESP32 field sensor node
// Libraries: "DHT sensor library" by Adafruit (install in Arduino IDE Library Manager)
// Wiring: DHT22 data -> GPIO 4 (10k pull-up), soil sensor AOUT -> GPIO 34, both on 3.3V and GND

#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

const char* WIFI_SSID  = "YOUR_WIFI_NAME";
const char* WIFI_PASS  = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL = "http://192.168.1.10:5000/api/readings"; // your laptop's IP
const char* API_KEY    = "demo-key-123";                          // from the farm page

#define DHTPIN 4
#define DHTTYPE DHT22
#define SOIL_PIN 34

const int SOIL_DRY_RAW = 3000;   // calibrate: reading in dry air
const int SOIL_WET_RAW = 1200;   // calibrate: reading in water
const unsigned long INTERVAL_MS = 60000;

DHT dht(DHTPIN, DHTTYPE);

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nConnected. IP: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  connectWiFi();
}

void loop() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) {
    Serial.println("DHT22 read failed, retrying...");
    delay(2000);
    return;
  }

  int raw = analogRead(SOIL_PIN);
  float soil = constrain(map(raw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100), 0, 100);

  if (WiFi.status() != WL_CONNECTED) connectWiFi();

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  String body = "{\"temperature\":" + String(t, 1) +
                ",\"humidity\":" + String(h, 1) +
                ",\"soil_moisture\":" + String(soil, 1) + "}";
  int code = http.POST(body);
  Serial.printf("POST %d  T=%.1f H=%.1f Soil=%.1f\n", code, t, h, soil);
  http.end();

  delay(INTERVAL_MS);
}
