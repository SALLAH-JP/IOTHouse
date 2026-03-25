#!/usr/bin/env python3
"""
IOT House — server.py
Lancer : python3 server.py
Ouvrir : https://localhost:5000
"""

import os
import json
import time
import threading
import subprocess
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ARDUINO_PORT = '/dev/ttyACM0'
ARDUINO_BAUD = 115200
OLLAMA_HOST  = 'http://11.0.0.10:11434'
OLLAMA_URL   = f'{OLLAMA_HOST}/api/chat'
OLLAMA_MODEL = 'domotique-assistant'
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
    'allumerLed':         ('salon',        True),
    'eteindreLed':        ('salon',        False),
    'allumerLedChambre':  ('chambre',      True),
    'eteindreLedChambre': ('chambre',      False),
    'allumerLedCuisine':  ('cuisine',      True),
    'eteindreLedCuisine': ('cuisine',      False),
    'allumerLedGarage':   ('garage-light', True),
    'eteindreLedGarage':  ('garage-light', False),
    'allumerMoteur':      ('fan',          True),
    'eteindreMoteur':     ('fan',          False),
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
Réponds UNIQUEMENT en JSON valide, sans texte avant ni après, sans balises markdown.

Si c'est une commande domotique, réponds :
{"type":"commande","reponse":"<confirmation courte>","action":"<action>","parametres":{"pièce":"<pièce>"}}

Actions disponibles :
- allumerLed / eteindreLed           → salon (RGB)
- allumerLedChambre / eteindreLedChambre
- allumerLedCuisine / eteindreLedCuisine
- allumerLedGarage  / eteindreLedGarage
- allumerTout / eteindreTout
- salonRouge / salonVert / salonBleu / salonBlanc
- allumerMoteur / eteindreMoteur     → ventilateur
- ventiloLent / ventiloRapide
- ouvrirGarage / fermerGarage

Pièces disponibles : salon, chambre, cuisine, garage

Si ce n'est pas une commande, réponds :
{"type":"chat","reponse":"<réponse courte en français>"}"""

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

    try:
        import serial
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        time.sleep(2)
        ser.write((cmd + '\n').encode())
        ser.close()

        print(f'[Arduino] ← {cmd}')
        return True

    except Exception as e:
        print(f'[Arduino] Erreur : {e}')
        return False

# ─────────────────────────────────────────────
# TTS
# ─────────────────────────────────────────────
def generate_tts(text: str):
    try:
        filename = f'tts_{int(time.time()*1000)}.wav'
        filepath = os.path.join(TTS_DIR, filename)

        script = f"""
import pyttsx3, sys
e = pyttsx3.init()
e.setProperty('rate', 160)
voices = e.getProperty('voices')
for v in voices:
    if 'fr' in v.id.lower() or 'french' in v.name.lower():
        e.setProperty('voice', v.id)
        break
e.save_to_file({json.dumps(text)}, {json.dumps(filepath)})
e.runAndWait()
"""
        result = subprocess.run(['python3', '-c', script], timeout=15, capture_output=True)

        if os.path.exists(filepath):
            return f'/tts/{filename}'
        else:
            print(f'[TTS] Fichier non généré. stderr: {result.stderr.decode()}')
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
        if action == 'allumerTout':
            for r in ['salon', 'chambre', 'cuisine', 'garage-light']:
                house_state[r] = True
        elif action == 'eteindreTout':
            for r in ['salon', 'chambre', 'cuisine', 'garage-light']:
                house_state[r] = False
        elif action in ACTION_STATE:
            room, on = ACTION_STATE[action]
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

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=init_arduino, daemon=True).start()

    print('=' * 50)
    print('IOT House server → https://localhost:5000')
    print(f'Arduino : {ARDUINO_PORT} @ {ARDUINO_BAUD}')
    print(f'Ollama  : {OLLAMA_URL} ({OLLAMA_MODEL})')
    print(f'TTS dir : {TTS_DIR}')
    print('=' * 50)

    app.run(host='0.0.0.0', port=5000, debug=False,
        ssl_context=('cert.pem', 'key.pem'))
