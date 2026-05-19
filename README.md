<div align="center">

# 🏠 IOTHouse

### *Maison connectée pilotée par la voix*

**Interface web vocale qui comprend vos commandes via un LLM et pilote les composants électroniques de votre maison via Arduino.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-HTTPS-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.org/)
[![Arduino](https://img.shields.io/badge/Arduino-Uno-00979D?logo=arduino&logoColor=white)](https://www.arduino.cc/)
[![Ollama](https://img.shields.io/badge/LLM-Mistral%20Large-7B68EE)](https://ollama.com/)

[**🎥 Voir la démo**](#-démonstration) · [**🚀 Installation**](#-installation) · [**📖 Documentation**](#-utilisation)

</div>

---

## 📺 Démonstration

> 🎬 **[▶️ Cliquez ici pour voir IOTHouse en action sur YouTube](https://youtu.be/fMAOpTnzdqo)**

[![IOTHouse Demo](https://img.youtube.com/vi/fMAOpTnzdqo/maxresdefault.jpg)](https://youtu.be/fMAOpTnzdqo)

*Démonstration du pilotage vocal d'une maison miniature : éclairage RGB par pièce, ventilateur, porte de garage, commandés en langage naturel.*

---

## 📋 Sommaire

- [À propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#%EF%B8%8F-architecture)
- [Matériel requis](#-matériel-requis)
- [Structure du projet](#-structure-du-projet)
- [Installation](#-installation)
- [Lancement](#%EF%B8%8F-lancement)
- [Utilisation](#-utilisation)
- [Format des réponses LLM](#-format-des-réponses-llm)
- [Actions disponibles](#%EF%B8%8F-actions-disponibles)
- [API HTTP](#-api-http)
- [Licence](#-licence)

---

## 🎯 À propos

IOTHouse est un **projet de groupe** d'**interface web vocale pour maison connectée**, développé à 3 dans le cadre académique à l'UDM. L'utilisateur parle dans son navigateur, sa voix est transcrite en texte, le texte est envoyé à un **LLM cloud** qui décide s'il s'agit d'une commande ou d'une conversation, puis l'action est exécutée sur un **Arduino** qui pilote les composants électroniques de la maison.

Le projet explore l'intégration de **Grands Modèles de Langage** dans des objets du quotidien pour offrir une **interaction naturelle** avec le matériel embarqué — un terrain d'expérimentation qui a servi de base au projet plus ambitieux [MARC](https://github.com/SALLAH-JP/MARC) (mon projet de fin de licence, en solo cette fois).

---

## ✨ Fonctionnalités

- 🎙️ **Reconnaissance vocale dans le navigateur** via la Web Speech API (aucun modèle à installer)
- 🧠 **LLM Mistral Large** via Ollama Cloud pour la compréhension du langage naturel
- 📋 **Sortie JSON structurée** : le LLM distingue automatiquement commande domotique et conversation
- 🔊 **Synthèse vocale** des réponses via **gTTS** (Google Text-to-Speech)
- 💡 **Pilotage Arduino** : LEDs RGB (couleurs personnalisables pour la chambre), ventilateur, porte garage
- 🌐 **Interface web HTTPS** accessible depuis tous les appareils du réseau
- 🔄 **Historique conversationnel** (6 derniers échanges) pour des dialogues cohérents
- 📊 **Suivi d'état temps réel** de chaque pièce côté serveur

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│  Navigateur                                 │
│  index.html · app.js · style.css            │
│  Web Speech API (STT)                       │
└──────────────────┬──────────────────────────┘
                   │ HTTPS · /send_text · /command
                   ▼
┌─────────────────────────────────────────────┐
│  Raspberry Pi 4 · server.py                 │
│  Flask HTTPS · gestion d'état maison        │
│  gTTS pour la synthèse vocale               │
└────────┬──────────────────────────┬─────────┘
         │                          │
         │ HTTP                     │ Série
         ▼                          ▼
┌─────────────────────┐    ┌────────────────────┐
│  Ollama Cloud       │    │  Arduino Uno       │
│  Mistral Large      │    │  LEDs · Moteurs    │
│  Sortie JSON        │    │  /dev/ttyACM0      │
└─────────────────────┘    └────────────────────┘
```

---

## 🔧 Matériel requis

| Composant | Détail |
| --- | --- |
| Raspberry Pi 4 | Pour faire tourner le serveur Flask |
| Arduino Uno | Connexion USB sur la Pi |
| LEDs (R, G, B) | 6 pièces : salon, chambre, cuisine, garage |
| Moteur DC | Ventilateur du salon |
| Moteur DC ou servo | Porte du garage |
| Pont en H L298N | Pilotage des moteurs DC |
| Microphone | Compatible navigateur (USB ou intégré) |
| Haut-parleur | Sortie audio pour la voix de l'assistant |

---

## 📁 Structure du projet

```
.
├── IOTHouse/              # Code Arduino
│   └── IOTHouse.ino       # Sketch (LEDs + Moteur DC + porte garage)
│
├── server.py              # Serveur Flask HTTPS
├── index.html             # Interface web de la maison
├── app.js                 # Logique JS (STT navigateur + appels API)
├── style.css              # Styles de l'interface
├── Modelfile              # Configuration du LLM Ollama
├── requirements.txt       # Dépendances Python
├── cert.pem               # Certificat SSL (à générer)
├── key.pem                # Clé privée SSL (à NE PAS commit)
└── LICENSE                # Licence MIT
```

---

## 🚀 Installation

### 1. Dépendances système

```bash
sudo apt update
sudo apt install python3-pip openssl -y
```

### 2. Dépendances Python

```bash
pip install -r requirements.txt
```

Les principales libs utilisées : `Flask`, `requests`, `gTTS`, `pyserial`.

### 3. Ollama Cloud

Le projet utilise **Mistral Large via Ollama Cloud** (`mistral-large-3:675b-cloud`).

```bash
# Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Se connecter à Ollama Cloud (clé API requise)
export OLLAMA_API_KEY="<votre_clé>"
export OLLAMA_HOST="https://ollama.com"
```

> 💡 Tu peux aussi utiliser un modèle local en remplaçant `OLLAMA_MODEL` dans `server.py` par exemple par `mistral` ou `qwen2.5:3b` pour une exécution 100% locale.

### 4. Arduino

Uploader le sketch `IOTHouse/IOTHouse.ino` sur l'Arduino via l'IDE Arduino ou `arduino-cli` :

```bash
arduino-cli core install arduino:avr
arduino-cli compile --fqbn arduino:avr:uno IOTHouse/
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno IOTHouse/
```

### 5. Certificat SSL

HTTPS est obligatoire pour accéder au microphone depuis le navigateur. Générer un certificat auto-signé :

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

> ⚠️ **Ne jamais commit `key.pem`** sur GitHub — c'est ta clé privée. Vérifier qu'elle est dans `.gitignore`.

---

## ▶️ Lancement

```bash
python3 server.py
```

Le serveur démarre sur `https://localhost:5000` (et `https://<ip-pi>:5000` depuis tout le réseau local).

Le navigateur affichera un avertissement de sécurité dû au certificat auto-signé — c'est normal sur un réseau local, accepter l'exception.

### Démarrage automatique au boot

Ajouter dans `crontab -e` :

```
@reboot cd /chemin/vers/IOTHouse && python3 server.py
```

---

## 📖 Utilisation

### Commande vocale

1. Ouvrir l'interface dans le navigateur
2. Cliquer sur le bouton micro
3. Énoncer une commande, par exemple :
   - *« Allume la lumière du salon »*
   - *« Mets la chambre en mauve »*
   - *« Ouvre la porte du garage »*
   - *« Éteins tout »*
   - *« Mets le ventilateur en mode rapide »*

L'assistant confirme oralement et exécute la commande sur l'Arduino.

### Commande clic

L'interface SVG de la maison permet de cliquer directement sur chaque pièce pour l'allumer/éteindre, sans passer par la voix.

### Conversation

Si la requête n'est pas une commande domotique, le LLM répond simplement par la voix sans actionner le matériel. Exemple :
- *« Quelle heure est-il ? »*
- *« Raconte-moi une blague »*

---

## 🤖 Format des réponses LLM

Le LLM est contraint de répondre **uniquement en JSON valide**, selon deux formats :

### Commande domotique

```json
{
  "type": "commande",
  "reponse": "Ok, j'allume le salon",
  "action": "allumerSalon"
}
```

### Couleur RGB pour la chambre

```json
{
  "type": "commande",
  "reponse": "Voilà ta chambre en mauve",
  "action": "allumerChambre 161 113 136"
}
```

### Conversation libre

```json
{
  "type": "chat",
  "reponse": "Il est 14h32 actuellement."
}
```

---

## 🎛️ Actions disponibles 

| Action | Description |
| --- | --- |
| `allumerSalon` / `eteindreSalon` | Lumière du salon (blanc par défaut) |
| `salonRouge` / `salonVert` / `salonBleu` | Salon en couleur fixe |
| `allumerChambre` / `eteindreChambre` | Lumière de la chambre |
| `allumerChambre <R> <G> <B>` | Chambre en couleur RGB personnalisée |
| `allumerCuisine` / `eteindreCuisine` | Lumière de la cuisine (rouge par défaut) |
| `allumerGarage` / `eteindreGarage` | Lumière du garage |
| `ouvrirGarage` / `fermerGarage` | Porte du garage motorisée |
| `allumerVentilo` / `eteindreVentilo` | Ventilateur du salon |
| `ventiloLent` / `ventiloRapide` | Vitesse du ventilateur |
| `allumerTout` / `eteindreTout` | Toutes les pièces et le ventilateur |

---

## 🌐 API HTTP

| Route | Méthode | Description |
| --- | --- | --- |
| `/` | GET | Interface web (`index.html`) |
| `/send_text` | POST | Pipeline vocal : `{ "user_text": "allume le salon" }` |
| `/command` | POST | Commande directe : `{ "command": "allumerSalon" }` |
| `/status` | GET | État courant : Arduino, modèle, état des pièces |
| `/tts/<filename>` | GET | Servir un fichier audio TTS généré |

### Réponse type de `/send_text`

```json
{
  "ai_reply": "Ok, j'allume le salon",
  "action": "allumerSalon",
  "type": "commande",
  "tts_url": "/tts/tts_1737054321000.mp3",
  "house_state": {
    "salon": true,
    "chambre": false,
    "cuisine": false,
    "garage-light": false,
    "garage-door": false,
    "fan": false
  }
}
```

---

## 🔌 Pipeline vocal

```
Navigateur
   │
   ▼
Web Speech API (STT)   ← reconnaissance vocale native du navigateur
   │
   ▼ POST /send_text
Flask server.py
   │
   ▼ HTTP
Mistral Large (Ollama Cloud)   ← LLM, sortie JSON contrainte
   │
   ├── type: commande  → série vers Arduino via /dev/ttyACM0
   │                      + mise à jour de house_state
   │
   └── type: chat      → gTTS → fichier MP3 → renvoyé au navigateur
                                   │
                                   ▼
                            Lecture dans le navigateur
```

---

## 🐛 Dépannage

**`could not open port /dev/ttyACM0`**
→ Vérifier le port avec `ls /dev/ttyACM* /dev/ttyUSB*` et adapter `ARDUINO_PORT` dans `server.py`.

**Le microphone ne s'active pas dans le navigateur**
→ Le HTTPS est obligatoire. Vérifier que `cert.pem` et `key.pem` sont bien présents et que tu accèdes à `https://` (pas `http://`).

**Erreur Ollama : 401 / 403**
→ Vérifier que `OLLAMA_API_KEY` est correctement exporté avant de lancer `server.py`.

**Pas de son lors de la réponse**
→ gTTS nécessite un accès Internet. Vérifier la connexion. Sinon basculer vers `espeak-ng` (fonction `generate_tts2` déjà présente dans le code).

---

## 👥 Équipe

Projet de groupe réalisé dans le cadre académique à l'**Université des Mascareignes** (Maurice), par 3 étudiants en 3ème année de Licence en Informatique Appliquée.

| Membre | Liens |
|--------|-------|
| **SALLAH Assiongbon Théodore Jean-Paul** | [![GitHub](https://img.shields.io/badge/GitHub-SALLAH--JP-181717?logo=github)](https://github.com/SALLAH-JP) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Jean--Paul%20SALLAH-0A66C2?logo=linkedin)](https://www.linkedin.com/in/jeanpaul-sallah/) |
| **RAKOTOMAVO Ny Vetso** | [![GitHub](https://img.shields.io/badge/GitHub-vetsojkr-181717?logo=github)](https://github.com/vetsojkr) |
| **RAZAFINDRATSIMBA Angelin Fehizoro** | [![GitHub](https://img.shields.io/badge/GitHub-angelin57-181717?logo=github)](https://github.com/angelin57) |

🎓 Université des Mascareignes — Maurice

---

## 🙏 Remerciements

- [Ollama](https://ollama.com) et le modèle **Mistral Large**
- [Flask](https://flask.palletsprojects.com)
- [gTTS](https://github.com/pndurette/gTTS) — Google Text-to-Speech (interface Python non officielle)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) — reconnaissance vocale navigateur

---

## 📜 Licence

Ce projet est distribué sous licence **MIT** — voir le fichier [`LICENSE`](LICENSE).

---

<div align="center">

*Si ce projet vous a plu, n'hésitez pas à laisser une ⭐ !*

</div>
