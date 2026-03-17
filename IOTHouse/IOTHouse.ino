// LED Salon RGB
const int LED_R = 2;
const int LED_G = 3;
const int LED_B = 11;

// LEDs simples
const int LED_CHAMBRE = 4;
const int LED_CUISINE = 7;
const int LED_GARAGE  = 8;

// Moteur 1 : Ventilateur
const int M1_IN1 = 5;
const int M1_IN2 = 6;

// Moteur 2 : Garage
const int M2_IN1 = 9;
const int M2_IN2 = 10;

void setup() {
  Serial.begin(115200);

  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(LED_CHAMBRE, OUTPUT);
  pinMode(LED_CUISINE, OUTPUT);
  pinMode(LED_GARAGE,  OUTPUT);
  pinMode(M1_IN1, OUTPUT);
  pinMode(M1_IN2, OUTPUT);
  pinMode(M2_IN1, OUTPUT);
  pinMode(M2_IN2, OUTPUT);

  // Tout éteint
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, LOW);
  digitalWrite(LED_B, LOW);
  digitalWrite(LED_CHAMBRE, LOW);
  digitalWrite(LED_CUISINE, LOW);
  digitalWrite(LED_GARAGE,  LOW);
  digitalWrite(M1_IN1, LOW);
  digitalWrite(M1_IN2, LOW);
  digitalWrite(M2_IN1, LOW);
  digitalWrite(M2_IN2, LOW);

  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();
    Serial.print("RECU:"); Serial.println(msg);

    // ── LED Salon RGB ──
    if (msg == "allumerLed" || msg == "LED") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:LED_SALON_ON");
    }
    else if (msg == "eteindreLed" || msg == "LED_OFF") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:LED_SALON_OFF");
    }
    else if (msg == "salonRouge") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:SALON_ROUGE");
    }
    else if (msg == "salonVert") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:SALON_VERT");
    }
    else if (msg == "salonBleu") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, HIGH);
      Serial.println("OK:SALON_BLEU");
    }
    else if (msg == "salonBlanc") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, HIGH);
      Serial.println("OK:SALON_BLANC");
    }

    // ── LEDs simples ──
    else if (msg == "allumerLedChambre") {
      digitalWrite(LED_CHAMBRE, HIGH);
      Serial.println("OK:LED_CHAMBRE_ON");
    }
    else if (msg == "eteindreLedChambre") {
      digitalWrite(LED_CHAMBRE, LOW);
      Serial.println("OK:LED_CHAMBRE_OFF");
    }
    else if (msg == "allumerLedCuisine") {
      digitalWrite(LED_CUISINE, HIGH);
      Serial.println("OK:LED_CUISINE_ON");
    }
    else if (msg == "eteindreLedCuisine") {
      digitalWrite(LED_CUISINE, LOW);
      Serial.println("OK:LED_CUISINE_OFF");
    }
    else if (msg == "allumerLedGarage") {
      digitalWrite(LED_GARAGE, HIGH);
      Serial.println("OK:LED_GARAGE_ON");
    }
    else if (msg == "eteindreLedGarage") {
      digitalWrite(LED_GARAGE, LOW);
      Serial.println("OK:LED_GARAGE_OFF");
    }

    // ── Tout allumer / éteindre ──
    else if (msg == "allumerTout") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      digitalWrite(LED_CHAMBRE, HIGH);
      digitalWrite(LED_CUISINE, HIGH);
      digitalWrite(LED_GARAGE,  HIGH);
      Serial.println("OK:TOUT_ON");
    }
    else if (msg == "eteindreTout") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      digitalWrite(LED_CHAMBRE, LOW);
      digitalWrite(LED_CUISINE, LOW);
      digitalWrite(LED_GARAGE,  LOW);
      Serial.println("OK:TOUT_OFF");
    }

    // ── Moteur 1 : Ventilateur ──
    else if (msg == "allumerMoteur" || msg == "MOTOR") {
      analogWrite(M1_IN1, 200);
      digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_ON");
    }
    else if (msg == "ventiloLent") {
      analogWrite(M1_IN1, 80);
      digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_SLOW");
    }
    else if (msg == "ventiloRapide") {
      analogWrite(M1_IN1, 255);
      digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_FAST");
    }
    else if (msg == "eteindreMoteur" || msg == "MOTOR_OFF") {
      digitalWrite(M1_IN1, LOW);
      digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_OFF");
    }

    // ── Moteur 2 : Garage ──
    else if (msg == "ouvrirGarage") {
      analogWrite(M2_IN1, 200);
      digitalWrite(M2_IN2, LOW);
      delay(2000);
      digitalWrite(M2_IN1, LOW);
      Serial.println("OK:GARAGE_OPEN");
    }
    else if (msg == "fermerGarage") {
      digitalWrite(M2_IN1, LOW);
      analogWrite(M2_IN2, 200);
      delay(2000);
      digitalWrite(M2_IN2, LOW);
      Serial.println("OK:GARAGE_CLOSE");
    }

    else {
      Serial.print("ERR:UNKNOWN:");
      Serial.println(msg);
    }
  }
}