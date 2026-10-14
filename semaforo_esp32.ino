// Semaforo ESP32 - WiFi HTTP hacia server.py (POST /api/state)
// Pines: ROJO=2 (20 s, exigido), AMARILLO=4 (5 s), VERDE=5 (15 s)
// El servidor Python expone POST /api/state y la web hace polling a GET /api/status.
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "TU_WIFI";
const char* WIFI_PASS = "TU_PASSWORD";
// IP de la PC donde corre: python server.py --no-serial
const char* SERVER_URL = "http://192.168.1.50:5000/api/state";

const int PIN_ROJO = 2;      // 20 s
const int PIN_AMARILLO = 4;  // 5 s
const int PIN_VERDE = 5;     // 15 s

const int DUR_ROJO = 20;
const int DUR_AMARILLO = 5;
const int DUR_VERDE = 15;

void setLights(bool r, bool y, bool g) {
  digitalWrite(PIN_ROJO, r ? HIGH : LOW);
  digitalWrite(PIN_AMARILLO, y ? HIGH : LOW);
  digitalWrite(PIN_VERDE, g ? HIGH : LOW);
}

void sendStatus(const char* stateName, int timeLeft, int duration) {
  // Debug por USB
  Serial.print("{\"state\":\"");
  Serial.print(stateName);
  Serial.print("\",\"time_left\":");
  Serial.print(timeLeft);
  Serial.print(",\"duration\":");
  Serial.print(duration);
  Serial.println("}");

  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  String body = String("{\"state\":\"") + stateName +
                String("\",\"time_left\":") + timeLeft +
                String(",\"duration\":") + duration + String("}");
  int code = http.POST(body);
  http.end();
  if (code < 0) {
    Serial.print("HTTP error: ");
    Serial.println(code);
  }
}

void runPhase(const char* stateName, bool r, bool y, bool g, int duration) {
  setLights(r, y, g);
  for (int t = duration; t > 0; t--) {
    sendStatus(stateName, t, duration);
    delay(1000);
  }
}

void setup() {
  pinMode(PIN_ROJO, OUTPUT);
  pinMode(PIN_AMARILLO, OUTPUT);
  pinMode(PIN_VERDE, OUTPUT);
  setLights(false, false, false);
  Serial.begin(115200);
  delay(300);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Conectando WiFi");
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println(WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "WiFi FALLO (sigo por Serial)");
}

void loop() {
  runPhase("GREEN", false, false, true, DUR_VERDE);     // verde 15 s
  runPhase("YELLOW", false, true, false, DUR_AMARILLO); // amarillo 5 s
  runPhase("RED", true, false, false, DUR_ROJO);       // rojo 20 s
}
