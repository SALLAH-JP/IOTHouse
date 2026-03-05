#!/usr/bin/env python3
"""
Voice Assistant: Real-Time Voice Chat

This app runs on a Raspberry Pi (or Linux desktop) and creates a low-latency, full-duplex voice interaction
with an AI character. It uses Google Speech Recognition, pyttsx3 TTS, and a locally hosted LLM via Ollama.

Copyright: M15.ai
License: MIT
"""

import os
import json
import threading
import time
import re
import requests
import numpy as np
import pyttsx3
import speech_recognition as sr

recognizer = sr.Recognizer()

# ------------------- TTS ENGINE -------------------

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

# ------------------- TIMING UTILITY -------------------

class Timer:
    def __init__(self, label):
        self.label = label
        self.enabled = True
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enabled:
            elapsed_ms = (time.time() - self.start) * 1000
            print(f"[Timing] {self.label}: {elapsed_ms:.0f} ms")
    def disable(self):
        self.enabled = False

# ------------------- PATHS -------------------

CONFIG_PATH = os.path.expanduser("va_config.json")
BASE_DIR    = os.path.dirname(__file__)

# ------------------- CONFIG -------------------

DEFAULT_CONFIG = {
    "volume": 9,
    "mic_name": "Plantronics",
    "audio_output_device": "Plantronics",
    "model_name": "robot-assistant",
    "voice": "en_US-kathleen-low.onnx",
    "enable_audio_processing": False,
    "history_length": 4,
    "system_prompt": "You are a helpful assistant."
}

def load_config():
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                user_config = json.load(f)
            return {**DEFAULT_CONFIG, **user_config}
        except Exception as e:
            print(f"[Warning] Failed to load system config: {e}")
    print("[Debug] Using default config.")
    return DEFAULT_CONFIG

config         = load_config()
VOLUME         = config["volume"]
MIC_NAME       = config["mic_name"]
MODEL_NAME     = config["model_name"]
HISTORY_LENGTH = config["history_length"]

VOICE_MODELS_DIR = os.path.join(BASE_DIR, 'voices')
if not os.path.isdir(VOICE_MODELS_DIR):
    os.makedirs(VOICE_MODELS_DIR)

VOICE_MODEL = os.path.join(VOICE_MODELS_DIR, config["voice"])

print('[Debug] Available Piper voices:')
for f in os.listdir(VOICE_MODELS_DIR):
    if f.endswith('.onnx'):
        print('  ', f)
print(f'[Debug] Using VOICE_MODEL: {VOICE_MODEL}')
print(f"[Debug] Config loaded: model={MODEL_NAME}, voice={config['voice']}, vol={VOLUME}, mic={MIC_NAME}")

messages = [{"role": "system", "content": config["system_prompt"]}]

# ------------------- STT : Google -------------------

def record_and_transcribe():
    with sr.Microphone() as source:
        print("[STT] 🎤 En écoute...")
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        audio = recognizer.listen(source)
    try:
        with Timer("STT"):
            import io
            import wave
            wav_data = io.BytesIO(audio.get_wav_data())
            audio_wav = sr.AudioData(wav_data.read(), audio.sample_rate, audio.sample_width)
            text = recognizer.recognize_google(audio_wav, language="fr-FR")
        print(f"[STT] Reconnu : {text}")
        return text
    except sr.UnknownValueError:
        print("[STT] Incompréhensible")
        return None
    except sr.RequestError as e:
        print(f"[STT] Erreur Google : {e}")
        return None

# ------------------- OLLAMA -------------------

def query_ollama():
    with Timer("Inference"):
        url     = "http://localhost:11434/api/generate"
        payload = {
            "model":  MODEL_NAME,
            "prompt": json.dumps(messages[-HISTORY_LENGTH:]),
            "stream": False
        }
        resp = requests.post(url, json=payload, timeout=30)

    response = resp.json()['response']
    print(f'[Debug] Ollama status: {response}')

    response = json.loads(response[response.find("{"):response.rfind("}")+1])

    if "action" in response:
        sendToArduino(response["action"])

    return response['reponse']

# ------------------- ARDUINO -------------------

def sendToArduino(cmd):
    try:
        import serial
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        ser.write((cmd + '\n').encode())
        ser.close()
        print(f"[Arduino] Commande envoyée : {cmd}")
    except Exception as e:
        print(f"[Arduino] Erreur : {e}")

# ------------------- TTS -------------------

def play_response(text):
    clean = re.sub(r"[\*]+",   '', text)
    clean = re.sub(r"\(.*?\)", '', clean)
    clean = re.sub(r"<.*?>",   '', clean)
    clean = clean.replace('\n', ' ').strip()
    clean = re.sub(r'\s+', ' ', clean)
    clean = re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]+', '', clean)

    with Timer("Playback"):
        done = threading.Event()

        def _speak():
            try:
                e = pyttsx3.init()
                v = e.getProperty('voices')
                e.setProperty('voice', v[0].id)
                e.setProperty('rate', 160)
                e.say(clean)
                e.runAndWait()
                e.stop()
            except Exception as ex:
                print(f"[Error] TTS: {ex}")
            finally:
                done.set()

        t = threading.Thread(target=_speak)
        t.start()
        done.wait(timeout=15)

    time.sleep(0.3)

# ------------------- PROCESSING LOOP -------------------

def processing_loop():
    MAX_DEBUG_LEN         = 200
    LOW_EFFORT_UTTERANCES = {"huh", "uh", "um", "erm", "hmm", "he's", "but"}

    while True:
        user = record_and_transcribe()

        if not user:
            continue

        if user.lower().strip(".,!? ") in LOW_EFFORT_UTTERANCES:
            print("[Debug] Ignored low-effort utterance.")
            continue

        print("User:", user)
        messages.append({"role": "user", "content": user})

        resp_text = query_ollama()
        if resp_text:
            clean_debug_text = resp_text.replace('\n', ' ').replace('\r', ' ')
            if len(clean_debug_text) > MAX_DEBUG_LEN:
                clean_debug_text = clean_debug_text[:MAX_DEBUG_LEN] + '...'
            print('Assistant:', clean_debug_text)
            messages.append({"role": "assistant", "content": clean_debug_text})
            play_response(resp_text)
        else:
            print('[Debug] Empty response, skipping TTS.')

# ------------------- MAIN -------------------

if __name__ == '__main__':
    t = threading.Thread(target=processing_loop, daemon=True)
    t.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nArrêt.")
