# 🏠 IOTHouse

Maison connectée pilotée par la voix, tournant entièrement en local sur une **Raspberry Pi 4**.  
L'assistant vocal comprend vos commandes, les interprète via un LLM, et pilote les composants électroniques (LEDs, moteur DC) via Arduino.

---

## 📐 Architecture du projet

```
IOTHouse/
├── Local-Voice/
│   ├── voice_assistant.py     # Pipeline vocal principal (STT → LLM → TTS)
│   ├── va_config.json         # Configuration (micro, modèle, voix...)
│   ├── vosk-model/            # Modèle de reconnaissance vocale (Vosk)
│   ├── voices/                # Modèles de synthèse vocale (Piper .onnx)
│   └── bin/piper/             # Binaire Piper TTS
│
├── matrixLed/
│   └── gif_viewer.py          # Affichage de GIFs sur matrice LED RGB (rpi-rgb-led-matrix)
│
├── web/
│   ├── index.html             # Interface web de la maison
│   ├── style.css              # Styles de l'interface
│   └── app.js                 # Logique JS (contrôles + appels backend)
│
└── Arduino/
    └── IOTHouse.ino           # Code Arduino (LED RGB + Moteur DC)
```

---

## 🔧 Matériel requis

| Composant | Détail |
|-----------|--------|
| Raspberry Pi 4 | 8 GB RAM recommandé |
| Arduino (Uno / Nano) | Connexion USB |
| LED RGB | Anodes communes ou cathodes |
| Pont en H L298N | Pilotage moteur DC |
| Moteur DC | Ventilateur / portail garage |
| Matrice LED RGB | 64×32, compatible rpi-rgb-led-matrix |
| Micro USB | Compatible PyAudio |
| Haut-parleur | Sortie audio via ALSA |

### Câblage Arduino

| Composant | Broche Arduino |
|-----------|---------------|
| LED Rouge | Pin 9 (PWM) |
| LED Verte | Pin 10 (PWM) |
| LED Bleue | Pin 11 (PWM) |
| Moteur IN1 | Pin 5 |
| Moteur IN2 | Pin 6 |
| Moteur EN  | Pin 3 (PWM) |

---

## 🚀 Installation

### 1. Dépendances système

```bash
sudo apt update
sudo apt install python3-dev python3-pip sox portaudio19-dev -y
```

### 2. Environnement Python

```bash
python3 -m venv env --system-site-packages
source env/bin/activate
pip install vosk ollama pyaudio pydub soxr numpy requests
```

> `--system-site-packages` est nécessaire pour accéder à `rgbmatrix` installé sur le système.

### 3. Matrice LED RGB (rpi-rgb-led-matrix)

```bash
sudo apt install python3-dev cython3 -y
make build-python
sudo make install-python
```

### 4. Piper TTS

Télécharger le binaire Piper et le placer dans `bin/piper/` :

```bash
mkdir -p bin/piper
# Télécharger depuis https://github.com/rhasspy/piper/releases
# Placer le binaire dans bin/piper/piper
```

Télécharger un modèle de voix `.onnx` dans le dossier `voices/`.

### 5. Vosk (reconnaissance vocale)

Télécharger un modèle Vosk dans `vosk-model/` :

```bash
# Modèle français léger recommandé :
# https://alphacephei.com/vosk/models → vosk-model-small-fr-0.22
```

### 6. Ollama + modèle LLM

```bash
# Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Modèle recommandé pour Pi 4 8GB (JSON strict, rapide)
ollama pull qwen2.5:3b

# Créer le modèle personnalisé avec le Modelfile
ollama create robot-assistant -f Modelfile
```

### 7. Arduino

```bash
# Installer arduino-cli
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
sudo mv bin/arduino-cli /usr/local/bin/

# Installer le core Arduino
arduino-cli core install arduino:avr

# Compiler et uploader
arduino-cli compile --fqbn arduino:avr:uno Arduino/IOTHouse/
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno Arduino/IOTHouse/
```

---

## ▶️ Lancement

```bash
# Depuis le dossier Local-Voice
source env/bin/activate
sudo env/bin/python3 voice_assistant.py
```

> `sudo` est nécessaire pour accéder à la matrice LED RGB (GPIO).

### Interface web

```bash
cd web/
python3 -m http.server 8080
# Ouvrir http://[ip-raspberry]:8080
```

---

## ⚙️ Configuration (`va_config.json`)

```json
{
  "volume": 9,
  "mic_name": "Plantronics",
  "audio_output_device": "Plantronics",
  "model_name": "robot-assistant",
  "voice": "fr_FR-upmc-medium.onnx",
  "enable_audio_processing": false,
  "history_length": 4,
  "system_prompt": "Tu es un assistant embarqué dans une maison connectée."
}
```

---

## 🤖 Format des réponses LLM (Modelfile)

Le modèle répond **uniquement en JSON** selon deux formats :

**Commande :**
```json
{
  "type": "commande",
  "reponse": "Ok, j'allume le salon",
  "action": "avancer",
  "paramètres": { "distance": 100 }
}
```

**Discussion :**
```json
{
  "type": "chat",
  "reponse": "Bonjour ! Comment puis-je vous aider ?"
}
```

### Actions disponibles

| Action | Description |
|--------|-------------|
| `avancer` | Avancer d'une distance |
| `reculer` | Reculer |
| `aller a droite` | Tourner à droite |
| `aller a gauche` | Tourner à gauche |
| `aller a un endroit x` | Aller à une destination |
| `se mettre en veille` | Mode veille |
| `changer le style d'yeux` | Changer l'expression |

---

## 🌐 Interface Web

L'interface affiche une illustration SVG de la maison avec les commandes associées.

| Contrôle | Commande Arduino |
|----------|-----------------|
| Salon — Lumière | `LED` / `LED_OFF` |
| Salon — Ventilateur | `MOTOR` / `MOTOR_OFF` |
| Garage — Lumière | `LED` / `LED_OFF` |
| Garage — Porte | `MOTOR` / `MOTOR_OFF` |
| Chambre | `LED` / `LED_OFF` |
| Cuisine | `LED` / `LED_OFF` |

Le backend doit exposer deux routes :

```python
POST /command   →  { "command": "LED" }
POST /voice     →  { "text": "allume le salon" }
GET  /status    →  { "salon": true, "chambre": false, ... }
```

---

## 🔌 Pipeline vocal

```
Micro
  │
  ▼
Vosk (STT)          ← reconnaissance vocale locale, modèle français
  │
  ▼
Ollama / qwen2.5    ← LLM local, répond en JSON
  │
  ├─ type: commande → sendToArduino() via /dev/ttyACM0
  │
  └─ type: chat     → Piper (TTS) → haut-parleur
```

---

## 🐛 Dépannage

**`ModuleNotFoundError: No module named 'rgbmatrix'`**
→ Utiliser `sudo env/bin/python3` pour accéder aux packages système.

**`ModuleNotFoundError: No module named 'vosk'`**
→ Bien activer l'environnement avec `source env/bin/activate` avant de lancer avec `sudo`.

**`could not open port /dev/ttyACM0`**
→ Vérifier le port avec `ls /dev/ttyACM* /dev/ttyUSB*`. Remplacer dans le code si nécessaire.

**Arduino ne reçoit pas les commandes**
→ Vérifier que le baud rate est identique dans le code Python (`115200`) et dans le sketch Arduino (`Serial.begin(115200)`).

---

## 📋 Dépendances Python

```
vosk
ollama
pyaudio
pydub
soxr
numpy
requests
pyserial
```

---

## 📄 Licence

MIT
