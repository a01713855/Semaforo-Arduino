const int PIN_ROJO = 2;      // 20 s (exigido)
const int PIN_AMARILLO = 3;  // 5 s
const int PIN_VERDE = 4;     // 15 s

const int DUR_ROJO = 20;
const int DUR_AMARILLO = 5;
const int DUR_VERDE = 15;

void setLights(bool r, bool y, bool g) {
  digitalWrite(PIN_ROJO, r ? HIGH : LOW);
  digitalWrite(PIN_AMARILLO, y ? HIGH : LOW);
  digitalWrite(PIN_VERDE, g ? HIGH : LOW);
}

// Envia: {"state":"RED","time_left":19,"duration":20}
void sendStatus(const char* state, int timeLeft, int duration) {
  Serial.print("{\"state\":\"");
  Serial.print(state);
  Serial.print("\",\"time_left\":");
  Serial.print(timeLeft);
  Serial.print(",\"duration\":");
  Serial.print(duration);
  Serial.println("}");
}

void runPhase(const char* state, bool r, bool y, bool g, int duration) {
  setLights(r, y, g);
  for (int t = duration; t > 0; t--) {
    sendStatus(state, t, duration);
    delay(1000);
  }
}

void setup() {
  pinMode(PIN_ROJO, OUTPUT);
  pinMode(PIN_AMARILLO, OUTPUT);
  pinMode(PIN_VERDE, OUTPUT);
  setLights(false, false, false);
  Serial.begin(9600);
  delay(500);
}

void loop() {
  runPhase("GREEN", false, false, true, DUR_VERDE);     // verde 15 s
  runPhase("YELLOW", false, true, false, DUR_AMARILLO); // amarillo 5 s
  runPhase("RED", true, false, false, DUR_ROJO);       // rojo 20 s
}
