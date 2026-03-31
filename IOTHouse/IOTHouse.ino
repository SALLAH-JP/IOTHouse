// LED Salon RGB
const int LED_R = 2;
const int LED_G = 8;
const int LED_B = 4;

// LEDs simples
const int LED_CUISINE = 7;
//const int LED_GARAGE  = 8;

// LED Chambre RGB
const int LED_CHAMBRE_R = 10;
const int LED_CHAMBRE_G = 11;
const int LED_CHAMBRE_B = 3;

// Moteur 1 : Ventilateur
const int M1_IN1 = 9;
//const int M1_IN2 = 10;

// Moteur 2 : Garage
const int M2_IN1 = 5;
const int M2_IN2 = 6;

void setup() {
  Serial.begin(115200);

  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(LED_CHAMBRE_R, OUTPUT);
  pinMode(LED_CHAMBRE_G, OUTPUT);
  pinMode(LED_CHAMBRE_B, OUTPUT);
  pinMode(LED_CUISINE, OUTPUT);
  pinMode(M1_IN1, OUTPUT);
  //pinMode(M1_IN2, OUTPUT);
  pinMode(M2_IN1, OUTPUT);
  pinMode(M2_IN2, OUTPUT);

  // Tout éteint
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_G, HIGH);
  digitalWrite(LED_B, HIGH);
  digitalWrite(LED_CHAMBRE_R, HIGH);
  digitalWrite(LED_CHAMBRE_G, HIGH);
  digitalWrite(LED_CHAMBRE_B, HIGH);
  digitalWrite(LED_CUISINE, HIGH);
  digitalWrite(M1_IN1, LOW);
  //digitalWrite(M1_IN2, LOW);
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
    if (msg == "allumerSalon" || msg == "LED") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:LED_SALON_ON");
    }
    else if (msg == "eteindreSalon" || msg == "LED_OFF") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, HIGH);
      Serial.println("OK:LED_SALON_OFF");
    }
    else if (msg == "salonRouge") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, HIGH);
      Serial.println("OK:SALON_ROUGE");
    }
    else if (msg == "salonVert") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, HIGH);
      Serial.println("OK:SALON_VERT");
    }
    else if (msg == "salonBleu") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:SALON_BLEU");
    }
    else if (msg == "salonBlanc") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      Serial.println("OK:SALON_BLANC");
    }

    // ── LEDs simples ──
    else if (msg == "allumerChambre") {
      digitalWrite(LED_CHAMBRE_R, LOW);
      digitalWrite(LED_CHAMBRE_G, LOW);
      digitalWrite(LED_CHAMBRE_B, LOW);
      Serial.println("OK:LED_CHAMBRE_ON");
    }
    else if (msg == "eteindreChambre") {
      digitalWrite(LED_CHAMBRE_R, HIGH);
      digitalWrite(LED_CHAMBRE_G, HIGH);
      digitalWrite(LED_CHAMBRE_B, HIGH);
      Serial.println("OK:LED_CHAMBRE_OFF");
    }
    else if (msg.startsWith("allumerChambre ")) {
        int r = msg.substring(15, msg.indexOf(' ', 15)).toInt();
        int reste = msg.indexOf(' ', 15) + 1;
        int g = msg.substring(reste, msg.indexOf(' ', reste)).toInt();
        int b = msg.substring(msg.lastIndexOf(' ') + 1).toInt();
        analogWrite(LED_CHAMBRE_R, 255 - r);
        analogWrite(LED_CHAMBRE_G, 255 - g);
        analogWrite(LED_CHAMBRE_B, 255 - b);
        Serial.println("OK:LED_CHAMBRE_RGB");
    }
    else if (msg == "allumerCuisine") {
      digitalWrite(LED_CUISINE, LOW);
      Serial.println("OK:LED_CUISINE_ON");
    }
    else if (msg == "eteindreCuisine") {
      digitalWrite(LED_CUISINE, HIGH);
      Serial.println("OK:LED_CUISINE_OFF");
    }

    // ── Tout allumer / éteindre ──
    else if (msg == "allumerTout") {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, LOW);
      digitalWrite(LED_B, LOW);
      digitalWrite(LED_CHAMBRE_R, LOW);
      digitalWrite(LED_CHAMBRE_G, LOW);
      digitalWrite(LED_CHAMBRE_B, LOW);
      digitalWrite(LED_CUISINE, LOW);
      analogWrite(M1_IN1, 60);
      Serial.println("OK:TOUT_ON");
    }
    else if (msg == "eteindreTout") {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, HIGH);
      digitalWrite(LED_B, HIGH);
      digitalWrite(LED_CHAMBRE_R, HIGH);
      digitalWrite(LED_CHAMBRE_G, HIGH);
      digitalWrite(LED_CHAMBRE_B, HIGH);
      digitalWrite(LED_CUISINE, HIGH);
      digitalWrite(M1_IN1, LOW);
      Serial.println("OK:TOUT_OFF");
    }

    // ── Moteur 1 : Ventilateur ──
    else if (msg == "allumerVentilo") {
      analogWrite(M1_IN1, 50);
      //digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_ON");
    }
    else if (msg == "ventiloLent") {
      analogWrite(M1_IN1, 20);
      //digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_SLOW");
    }
    else if (msg == "ventiloRapide") {
      analogWrite(M1_IN1, 100);
      //digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_FAST");
    }
    else if (msg == "eteindreVentilo") {
      digitalWrite(M1_IN1, LOW);
      //digitalWrite(M1_IN2, LOW);
      Serial.println("OK:MOTOR1_OFF");
    }

    // ── Moteur 2 : Garage ──
    else if (msg == "ouvrirGarage") {
      for (int i = 0; i < 80; i++) {
        analogWrite(M2_IN1, 75);
        digitalWrite(M2_IN2, LOW);
        delay(20);
        digitalWrite(M2_IN1, LOW);
        delay(20);
      }
      Serial.println("OK:GARAGE_OPEN");
    }
    else if (msg == "fermerGarage") {
      for (int i = 0; i < 60; i++) {
        digitalWrite(M2_IN1, LOW);
        analogWrite(M2_IN2, 75);
        delay(20);
        digitalWrite(M2_IN2, LOW);
        delay(20);
      }
      Serial.println("OK:GARAGE_CLOSE");
    }

    else {
      Serial.print("ERR:UNKNOWN:");
      Serial.println(msg);
    }
  }
}
