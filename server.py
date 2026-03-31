#!/usr/bin/env python3
"""
IOT House — server.py
Lancer : python3 server.py
Ouvrir : https://localhost:5000
"""


import re
import os
import json
import time
import threading
import subprocess
import requests
from gtts import gTTS
from flask import Flask, request, jsonify, send_from_directory


app = Flask(__name__, static_folder='.')

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ARDUINO_PORT = '/dev/ttyACM0'
ARDUINO_BAUD = 115200
OLLAMA_HOST  = 'http://localhost:11434'
OLLAMA_URL   = f'{OLLAMA_HOST}/api/chat'
OLLAMA_MODEL = 'mistral-large-3:675b-cloud'
TTS_DIR      = os.path.join(os.path.dirname(__file__), 'tts_cache')
HISTORY_LEN  = 6

os.makedirs(TTS_DIR, exist_ok=True)
messages = []

# ─────────────────────────────────────────────
# ÉTAT MAISON
# ─────────────────────────────────────────────
house_state = {
    'salon':        False,
    'chambre':      False,
    'cuisine':      False,
    'garage-light': False,
    'garage-door':  False,
    'fan':          False,
}

ACTION_STATE = {
    'allumerSalon':         ('salon',        True),
    'eteindreSalon':        ('salon',        False),
    'allumerChambre':  ('chambre',      True),
    'eteindreChambre': ('chambre',      False),
    'allumerCuisine':  ('cuisine',      True),
    'eteindreCuisine': ('cuisine',      False),
    'allumerGarage':   ('garage-light', True),
    'eteindreGarage':  ('garage-light', False),
    'allumerVentilo':     ('fan',          True),
    'eteindreVentilo':    ('fan',          False),
    'ventiloLent':        ('fan',          True),
    'ventiloRapide':      ('fan',          True),
    'ouvrirGarage':       ('garage-door',  True),
    'fermerGarage':       ('garage-door',  False),
    'salonRouge':         ('salon',        True),
    'salonVert':          ('salon',        True),
    'salonBleu':          ('salon',        True),
    'salonBlanc':         ('salon',        True),
}

SYSTEM_PROMPT = """Tu es un assistant domotique pour une maison connectée.
Réponds UNIQUEMENT en JSON valide, sans texte avant ni après, sans balises markdown, avec une seul action.

Si c'est une commande domotique, réponds :
{"type":"commande","reponse":"<confirmation un peu courte>","action":"<action>"}

Actions disponibles :
- allumerSalon : pour allumer la lumière du salon en blanc
- eteindreSalon : pour éteindre la lumière de la chanbre
- allumerChambre : pour allumer la lumière de la chambre en blanc
- eteindreChambre : pour éteindre le lumière de la chambre
- allumerCuisine : pour allumer la lumière de la cuisine uniquement en rouge
- eteindreCuisine : pour éteindre la lumière de la cuisine
- allumerTout : pour allumer toutes les lumières et le ventilateur
- eteindreTout : pour éteindre toutes les lumières et le ventilateur
- salonRouge : pour allumer la lumière du salon en rouge
- salonVert : pour allumer la lumière du salon en vert
- salonBleu : pour allumer la lumière du salon en bleu
- allumerVentilo : pour allumer le ventilateur dans le salon dans le mode par défaut
- eteindreVentilo : pour éteindre le ventilateur dans salon
- ventiloLent : pour allumer le ventilateur en mode lent dans salon
- ventiloRapide : pour allumer le ventilateur en mode rapide dans salon
- ouvrirGarage : pour ouvrir la porte du garage
- fermerGarage : pour fermer la porte du garage

Autres : Pour la chambre et uniquement pour la chambre tu peux spécifier un code RGB si l'utilisateur veut allumer la lumière de la chambre dans une couleur particulière, exemple pour du mauve:
{"type":"commande", "reponse":"<confirmation un peu courte>","action":"allumerChambre 161 113 136"
Si ce n'est pas une commande, réponds :
{"type":"chat","reponse":"<réponse moyennement courte en français>"}"""

# ─────────────────────────────────────────────
# ARDUINO
# ─────────────────────────────────────────────
arduino = None

def init_arduino():
    global arduino
    try:
        import serial
        arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=2)
        time.sleep(2)
        arduino.reset_input_buffer()
        print(f'[Arduino] Connecté sur {ARDUINO_PORT} ✓')
    except Exception as e:
        print(f'[Arduino] Non connecté (ignoré) : {e}')
        arduino = None

def send_to_arduino(cmd: str):
    global arduino
    if arduino is None:
        print(f'[Arduino] Ignoré (non connecté) : {cmd}')
        return False
    try:
        arduino.reset_input_buffer()
        arduino.write((cmd + '\n').encode())
        response = arduino.readline().decode().strip()
        print(f'[Arduino] ← {cmd}')
        print(f'[Arduino] → {response}')
        return True
    except Exception as e:
        print(f'[Arduino] Erreur : {e}')
        arduino = None
        return False

# ─────────────────────────────────────────────
# TTS
# ─────────────────────────────────────────────
def clean_tts_text(text: str) -> str:
    # Supprimer les caractères problématiques
    text = text.replace('?', '').replace('!', '')
    text = text.replace('...', ' ').replace('..', ' ')
    text = re.sub(r'[^\w\s,.\'-àâäéèêëîïôùûüç]', '', text, flags=re.UNICODE)
    return text.strip()

def generate_tts2(text: str):
    try:
        filename = f'tts_{int(time.time()*1000)}.wav'
        filepath = os.path.join(TTS_DIR, filename)

        subprocess.run(
            ['espeak-ng', '-v', 'fr', '-s', '140', '-w', filepath, text],
            timeout=10, capture_output=True
        )

        if os.path.exists(filepath):
            return f'/tts/{filename}'
        return None

    except Exception as e:
        print(f'[TTS] Erreur : {e}')
        return None

def generate_tts(text: str):
    try:
        filename = f'tts_{int(time.time()*1000)}.mp3'
        filepath = os.path.join(TTS_DIR, filename)
        gTTS(text=text, lang='fr').save(filepath)
        if os.path.exists(filepath):
            return f'/tts/{filename}'
        return None
    except Exception as e:
        print(f'[TTS] Erreur : {e}')
        return None


# ─────────────────────────────────────────────
# OLLAMA
# ─────────────────────────────────────────────
def query_ollama(user_text: str) -> dict:
    global messages
    messages.append({'role': 'user', 'content': user_text})
    prompt_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages[-HISTORY_LEN:]
    try:
        resp = requests.post(OLLAMA_URL, json={
            'model': OLLAMA_MODEL, 'messages': prompt_messages, 'stream': False
        }, timeout=30)
        raw = resp.json()['message']['content']
        print(f'[Ollama] raw: {raw}')
        start, end = raw.find('{'), raw.rfind('}')
        if start == -1 or end == -1:
            raise ValueError(f'Pas de JSON dans : {raw}')
        parsed = json.loads(raw[start:end+1])
        messages.append({'role': 'assistant', 'content': raw})
        return parsed
    except Exception as e:
        print(f'[Ollama] Erreur : {e}')
        return {'type': 'chat', 'reponse': "Désolé, je n'ai pas compris."}

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    if filename.startswith(('send_text', 'command', 'tts/', 'status')):
        return jsonify({'error': 'not found'}), 404
    try:
        return send_from_directory('.', filename)
    except Exception:
        return jsonify({'error': 'not found'}), 404

@app.route('/tts/<filename>')
def serve_tts(filename):
    return send_from_directory(TTS_DIR, filename)

@app.route('/send_text', methods=['POST'])
def send_text():
    data      = request.get_json()
    user_text = data.get('user_text', '').strip()

    if not user_text:
        return jsonify({'error': 'Texte vide'}), 400

    print(f'[Voice] "{user_text}"')

    result     = query_ollama(user_text)
    ai_reply   = result.get('reponse', '')
    action     = result.get('action', None)
    parametres = result.get('parametres', {})

    # Màj house_state + envoyer à l'Arduino
    if action:
        base_action = action.split()[0]

        if base_action == 'allumerTout':
            for r in ['salon', 'chambre', 'cuisine', 'fan']:
                house_state[r] = True
        elif base_action == 'eteindreTout':
            for r in ['salon', 'chambre', 'cuisine', 'fan']:
                house_state[r] = False
        elif base_action in ACTION_STATE:
            room, on = ACTION_STATE[base_action]
            house_state[room] = on
        send_to_arduino(action)

    tts_url = generate_tts(ai_reply) if ai_reply else None

    return jsonify({
        'ai_reply':    ai_reply,
        'action':      action,
        'parametres':  parametres,
        'type':        result.get('type', 'chat'),
        'tts_url':     tts_url,
        'house_state': house_state,
    })

@app.route('/command', methods=['POST'])
def command():
    data = request.get_json()
    cmd  = data.get('command', '')

    # Màj house_state
    if cmd == 'allumerTout':
        for r in ['salon', 'chambre', 'cuisine', 'garage-light']:
            house_state[r] = True
    elif cmd == 'eteindreTout':
        for r in ['salon', 'chambre', 'cuisine', 'garage-light']:
            house_state[r] = False
    elif cmd in ACTION_STATE:
        room, on = ACTION_STATE[cmd]
        house_state[room] = on

    ok = send_to_arduino(cmd)
    return jsonify({'ok': bool(ok), 'command': cmd, 'house_state': house_state})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'ok':          True,
        'arduino':     arduino is not None and arduino.is_open if arduino else False,
        'ollama':      OLLAMA_URL,
        'model':       OLLAMA_MODEL,
        'house_state': house_state,
    })



print('=' * 50)
print('IOT House server → https://localhost:5000')
print(f'Arduino : {ARDUINO_PORT} @ {ARDUINO_BAUD}')
print(f'Ollama  : {OLLAMA_URL} ({OLLAMA_MODEL})')
print(f'TTS dir : {TTS_DIR}')
print('=' * 50)

init_arduino()


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000, debug=False)
