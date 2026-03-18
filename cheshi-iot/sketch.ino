#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASS = "";

const char* MQTT_SERVER = "chameleon.lmq.cloudamqp.com";
const int MQTT_PORT     = 8883;
const char* MQTT_USER   = "nepbljkj:nepbljkj";
const char* MQTT_PASS   = "CGrqBOuLe6sRAvbl8VgRVl5yXsJ6chV6";
const char* MQTT_TOPIC  = "iot/telemetry";

WiFiClientSecure wifiClient;
PubSubClient     client(wifiClient);

// --- Device identity ---
String deviceId   = "meter-esp32-001";
String region     = "north";
String deviceType = "smart-energy-meter";

// ----------------------------------------------------------------
// WiFi & MQTT helpers (tidak berubah dari versi asli)
// ----------------------------------------------------------------
void connectWifi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect(deviceId.c_str(), MQTT_USER, MQTT_PASS)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2s");
      delay(2000);
    }
  }
}

// ----------------------------------------------------------------
// Utility: random float dalam rentang [minVal, maxVal]
// ----------------------------------------------------------------
float randomFloat(float minVal, float maxVal) {
  return minVal + ((float)random(0, 10000) / 10000.0) * (maxVal - minVal);
}

// ----------------------------------------------------------------
// publishTelemetry — kirim data energy monitoring ke MQTT broker
//
// Perubahan dari versi agriculture:
//   - temperature, humidity, soil_moisture, battery  --> DIHAPUS
//   - voltage, current, power, energy,
//     power_factor, frequency                        --> DITAMBAHKAN
//   - power dihitung dari P = V x I (sesuai PDF)
//
// Range nilai mengacu pada standar PLN 220 V / 50 Hz:
//   voltage      : 218 – 242 V  (toleransi ±5%)
//   current      : 0.5 – 16 A   (beban rumah tangga / ringan industri)
//   power_factor : 0.80 – 0.99
//   frequency    : 49.8 – 50.2 Hz
//   energy       : akumulasi kWh, bertambah tiap siklus
// ----------------------------------------------------------------
static float accumulatedEnergy = 0.0;  // kWh, simulasi akumulasi

void publishTelemetry() {
  // Ukur parameter listrik
  float voltage      = randomFloat(218.0, 242.0);
  float current      = randomFloat(0.5, 16.0);
  float power_factor = randomFloat(0.80, 0.99);
  float frequency    = randomFloat(49.8, 50.2);

  // P = V x I  (Watt) — sesuai rumus di PDF
  float power = voltage * current;

  // Akumulasi energi: E += P * dt  (dt = 5 s = 5/3600 jam)
  accumulatedEnergy += power * (5.0 / 3600.0 / 1000.0);  // konversi ke kWh

  // Bangun JSON payload
  // Ukuran doc diperbesar ke 300 karena field lebih banyak
  StaticJsonDocument<300> doc;

  doc["device_id"]    = deviceId;
  doc["region"]       = region;
  doc["device_type"]  = deviceType;
  doc["voltage"]      = round(voltage * 10) / 10.0;       // 1 desimal
  doc["current"]      = round(current * 100) / 100.0;     // 2 desimal
  doc["power"]        = round(power * 10) / 10.0;         // Watt, 1 desimal
  doc["energy"]       = round(accumulatedEnergy * 1000) / 1000.0; // kWh, 3 desimal
  doc["power_factor"] = round(power_factor * 100) / 100.0;
  doc["frequency"]    = round(frequency * 10) / 10.0;

  char buffer[300];
  serializeJson(doc, buffer);

  bool ok = client.publish(MQTT_TOPIC, buffer);
  if (ok) {
    Serial.print("[PUB] ");
    Serial.println(buffer);
  } else {
    Serial.println("[ERR] publish failed");
  }
}

// ----------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  connectWifi();

  // Workshop/demo shortcut: skip certificate validation.
  // Good for demo use, not for production.
  wifiClient.setInsecure();

  client.setServer(MQTT_SERVER, MQTT_PORT);

  randomSeed(micros());

  connectMQTT();
}

void loop() {
  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  static unsigned long lastPublish = 0;
  if (millis() - lastPublish >= 5000) {
    lastPublish = millis();
    publishTelemetry();
  }
}
