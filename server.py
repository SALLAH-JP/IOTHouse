#!/usr/bin/env python3
"""
IOT House — server.py
Flask backend :
  GET  /              → interface web
  POST /send_text     → Ollama → TTS → retourne {ai_reply, action, tts_url}
  POST /command       → Arduino direct
  GET  /tts/<file>    → sert le fichier audio généré

Lancer : python3 server.py
Ouvrir : http://localhost:5000
"""

import os
import json
import time
import subprocess
import re
import requests
import ollama
import speech_recognition as sr
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')
recognizer = sr.Recognizer()

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
ARDUINO_PORT  = '/dev/ttyACM0'   # Windows: 'COM3', 'COM4', etc.
ARDUINO_BAUD  = 115200
OLLAMA_URL    = 'http://10.127.146.125:11434/api/generate'
OLLAMA_MODEL  = 'qwen2.5:1.5b'
TTS_DIR       = os.path.join(os.path.dirname(__file__), 'tts_cache')
HISTORY_LEN   = 6

os.makedirs(TTS_DIR, exist_ok=True)

# Historique conversation
messages = []

SYSTEM_PROMPT = """Tu es un assistant domotique pour une maison connectée.
Réponds UNIQUEMENT en JSON valide, sans texte avant ni après, sans balises markdown.

Si c'est une commande domotique, réponds :
{"type":"commande","reponse":"<confirmation courte>","action":"<action>","parametres":{"pièce":"<pièce>"}}

Actions disponibles : allumerLed, eteindreLed, allumerMoteur, eteindreMoteur, ouvrirGarage, fermerGarage
Pièces disponibles : salon, chambre, cuisine, garage

Si ce n'est pas une commande, réponds :
{"type":"chat","reponse":"<réponse courte en français>"}"""

# ─────────────────────────────────────────────
# ARDUINO
# ─────────────────────────────────────────────
def send_to_arduino(cmd: str):
    try:
        import serial
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        time.sleep(0.1)
        ser.write((cmd + '\n').encode())
        ser.close()
        print(f'[Arduino] ← {cmd}')
        return True
    except Exception as e:
        print(f'[Arduino] Erreur : {e}')
        return False

# ─────────────────────────────────────────────
# TTS avec pyttsx3 (local, offline)
# ─────────────────────────────────────────────
def generate_tts(text: str) -> str | None:
    """Génère un fichier MP3 depuis le texte, retourne le chemin relatif."""
    try:
        filename = f'tts_{int(time.time()*1000)}.wav'
        filepath = os.path.join(TTS_DIR, filename)

        # Utilise pyttsx3 via subprocess pour éviter les problèmes de thread
        script = f"""
import pyttsx3, sys
e = pyttsx3.init()
e.setProperty('rate', 160)
voices = e.getProperty('voices')
# Cherche une voix française
for v in voices:
    if 'fr' in v.id.lower() or 'french' in v.name.lower():
        e.setProperty('voice', v.id)
        break
e.save_to_file({json.dumps(text)}, {json.dumps(filepath)})
e.runAndWait()
"""
        result = subprocess.run(
            ['python3', '-c', script],
            timeout=15,
            capture_output=True
        )

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
        resp = requests.post(
            'http://localhost:11434/api/chat',
            json={
                'model':    OLLAMA_MODEL,
                'messages': prompt_messages,
                'stream':   False,
            },
            timeout=30
        )

        raw = resp.json()['message']['content']
        print(f'[Ollama] raw: {raw}')

        start = raw.find('{')
        end   = raw.rfind('}')
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
    # Ne pas intercepter les routes API
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

    # Appel Ollama
    result = query_ollama(user_text)

    ai_reply  = result.get('reponse', '')
    action    = result.get('action', None)
    parametres = result.get('parametres', {})

    # Envoyer à l'Arduino si commande
    if action:
        send_to_arduino(action)

    # Générer TTS
    tts_url = None
    if ai_reply:
        tts_url = generate_tts(ai_reply)

    return jsonify({
        'ai_reply':   ai_reply,
        'action':     action,
        'parametres': parametres,
        'type':       result.get('type', 'chat'),
        'tts_url':    tts_url,
    })

@app.route('/command', methods=['POST'])
def command():
    data = request.get_json()
    cmd  = data.get('command', '')
    ok   = send_to_arduino(cmd)
    return jsonify({'ok': ok, 'command': cmd})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'ok': True})


@app.route('/listen', methods=['POST'])
def listen():
    try:
        with sr.Microphone() as source:
            print('[Pi Mic] En écoute...')
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)

        # Choix : Google (internet) ou Vosk (local)
        transcript = recognizer.recognize_google(audio, language='fr-FR')
        # transcript = recognizer.recognize_vosk(audio)  # ← 100% local

        print(f'[Pi Mic] Transcrit : "{transcript}"')
        if not transcript:
            return jsonify({'error': 'Rien entendu'}), 200

        result     = query_ollama(transcript)
        ai_reply   = result.get('reponse', '')
        action     = result.get('action', None)
        parametres = result.get('parametres', {})

        if action:
            send_to_arduino(action)

        tts_url = generate_tts(ai_reply) if ai_reply else None

        return jsonify({
            'transcript': transcript,
            'ai_reply':   ai_reply,
            'action':     action,
            'parametres': parametres,
            'tts_url':    tts_url,
        })

    except sr.WaitTimeoutError:
        return jsonify({'error': 'Temps écoulé, rien entendu'})
    except sr.UnknownValueError:
        return jsonify({'error': 'Incompréhensible'})
    except Exception as e:
        print(f'[Pi Mic] Erreur : {e}')
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 50)
    print('IOT House server → http://localhost:5000')
    print(f'Arduino : {ARDUINO_PORT} @ {ARDUINO_BAUD}')
    print(f'Ollama  : {OLLAMA_URL} ({OLLAMA_MODEL})')
    print(f'TTS dir : {TTS_DIR}')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
