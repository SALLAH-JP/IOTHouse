void setup() {
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    String message = Serial.readStringUntil('\n');
    Serial.println("Recu: " + message);
  }
}