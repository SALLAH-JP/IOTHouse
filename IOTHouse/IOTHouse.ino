// Broches LED RGB
const int PIN_R = 9;
const int PIN_G = 10;
const int PIN_B = 11;

// Broches Moteur DC (L298N)
const int MOTOR_IN1 = 5;
const int MOTOR_IN2 = 6;
const int MOTOR_EN  = 3;

void setup() {
  Serial.begin(115200);

  pinMode(PIN_R, OUTPUT);
  pinMode(PIN_G, OUTPUT);
  pinMode(PIN_B, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(MOTOR_EN, OUTPUT);
}

void loop() {
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();

    if (msg == "LED") {
      analogWrite(PIN_R, 255);
      analogWrite(PIN_G, 0);
      analogWrite(PIN_B, 0);
      Serial.println("LED allumée");
    }
    else if (msg == "MOTOR") {
      analogWrite(MOTOR_EN, 200);
      digitalWrite(MOTOR_IN1, HIGH);
      digitalWrite(MOTOR_IN2, LOW);
      Serial.println("Moteur démarré");
    }
    else {
      Serial.println("Commande inconnue");
    }
  }
}