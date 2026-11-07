// BMO front-panel buttons -> serial. Works on Uno, Nano, Pro Micro (and most Arduino boards).
// Wire each button between its pin and GND. No resistors needed (internal pull-ups).
const char* NAMES[] = {"up", "down", "left", "right", "green", "red", "triangle"};
const uint8_t PINS[] = { 2,    3,      4,      5,       6,       7,     8 };
const uint8_t N = 7;

bool last[N];
unsigned long changedAt[N];

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < N; i++) {
    pinMode(PINS[i], INPUT_PULLUP);
    last[i] = false;
  }
}

void loop() {
  for (uint8_t i = 0; i < N; i++) {
    bool pressed = digitalRead(PINS[i]) == LOW;
    if (pressed != last[i] && millis() - changedAt[i] > 20) {   // 20 ms debounce
      last[i] = pressed;
      changedAt[i] = millis();
      Serial.print(NAMES[i]);
      Serial.println(pressed ? " 1" : " 0");                     // e.g. "green 1" / "green 0"
    }
  }
}
