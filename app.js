// ===================================================
//  IOT House — app.js
//  Les boutons envoient au serveur via /command
//  La voix envoie au serveur via /send_text
//  Le serveur retourne house_state → appliqué sur l'UI
// ===================================================

const roomWindows = {
  salon:   'win-salon',
  chambre: 'win-chambre',
  cuisine: 'win-cuisine',
};

const windowClass = {
  salon:   'salon-on',
  chambre: 'chambre-on',
  cuisine: 'cuisine-on',
};

const commands = {
  salon:          { on: 'allumerLed',       off: 'eteindreLed'       },
  fan:            { on: 'allumerVentilo',   off: 'eteindreVentilo'    },
  'garage-light': { on: 'allumerLedGarage', off: 'eteindreLedGarage' },
  'garage-door':  { on: 'ouvrirGarage',     off: 'fermerGarage'      },
  chambre:        { on: 'allumerLedChambre',off: 'eteindreLedChambre' },
  cuisine:        { on: 'allumerLedCuisine',off: 'eteindreLedCuisine' },
};

// ── Appliquer l'état reçu du serveur sur l'UI ──
function applyHouseState(s) {
  if (!s) return;
  ['salon', 'chambre', 'cuisine', 'garage-light', 'garage-door', 'fan'].forEach(room => {
    if (!(room in s)) return;
    const on   = s[room];
    const cb   = document.getElementById('toggle-' + room);
    const card = document.getElementById('card-' + room);
    if (cb)   cb.checked = on;
    if (card) card.classList.toggle('active', on);

    const winId = roomWindows[room];
    if (winId) {
      const el = document.getElementById(winId);
      if (el) {
        el.classList.remove('off', 'salon-on', 'chambre-on', 'cuisine-on');
        el.classList.add(on && windowClass[room] ? windowClass[room] : 'off');
      }
    }

    if (room === 'garage-light') {
      const interior = document.getElementById('garage-interior');
      if (interior) interior.style.opacity = on ? '0.22' : '0';
    }
    if (room === 'garage-door') animateGarage(on);
    if (room === 'fan')         animateFan(on);
  });
}

// ── Envoyer une commande au serveur (boutons) ──
async function sendCommand(cmd, room) {
  addLog(`${room.toUpperCase()} → ${cmd}`, 'cmd');
  try {
    const res = await fetch('/command', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ command: cmd }),
    });
    const data = await res.json();
    if (data.house_state) applyHouseState(data.house_state);
    addLog('Arduino ✓', 'info');
  } catch {
    addLog('[démo] simulation locale', 'info');
  }
}

// ── Boutons room-card ──
document.querySelectorAll('.room-card').forEach(card => {
  const room = card.dataset.room;

  card.addEventListener('click', e => {
    if (e.target.closest('.toggle')) return;
    const cb = document.getElementById('toggle-' + room);
    const on = cb ? !cb.checked : false;
    sendCommand(on ? commands[room].on : commands[room].off, room);
  });

  const cb = document.getElementById('toggle-' + room);
  if (cb) cb.addEventListener('change', () => {
    sendCommand(cb.checked ? commands[room].on : commands[room].off, room);
  });
});

// ── FAN ──
function animateFan(on) {
  const group  = document.getElementById('fan-group');
  const blades = document.getElementById('fan-blades');
  if (!group || !blades) return;

  if (on) {
    group.style.opacity = '1';
    blades.classList.add('spinning');
  } else {
    blades.classList.remove('spinning');
    group.style.opacity = '0.35';
  }
}

// ── GARAGE ──
function animateGarage(open) {
  [1,2,3,4].forEach(i => {
    const p = document.getElementById('garage-panel-' + i);
    if (!p) return;
    setTimeout(() => {
      p.style.transform = open ? 'scaleY(0)' : 'scaleY(1)';
      p.style.opacity   = open ? '0' : '1';
    }, i * 90);
  });
}

// ── PUSH-TO-TALK ──
let recognition = null;
const micBtn     = document.getElementById('micBtn');
const micStatus  = document.getElementById('micStatus');
const userTextEl = document.getElementById('userText');
const aiReplyEl  = document.getElementById('aiReply');

function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { addLog('Web Speech API non supportée — utilise Chrome', 'err'); return null; }

  const rec = new SR();
  rec.continuous = false; rec.interimResults = false; rec.lang = 'fr-FR';

  rec.onresult = async (event) => {
    const transcript = event.results[0][0].transcript.trim();
    userTextEl.textContent = transcript;
    setMicStatus('Traitement…', 'processing');
    addLog(`Voix : "${transcript}"`, 'info');

    try {
      const res  = await fetch('/send_text', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ user_text: transcript }),
      });
      const data = await res.json();

      aiReplyEl.textContent = data.ai_reply || '';
      if (data.action)      addLog(`Action : ${data.action}`, 'cmd');
      if (data.house_state) applyHouseState(data.house_state);
      if (data.tts_url)     new Audio(data.tts_url).play().catch(console.error);
      addLog(`IA : ${(data.ai_reply || '').slice(0, 80)}`, 'info');

    } catch (e) {
      addLog('Erreur serveur : ' + e.message, 'err');
    }
    setMicStatus('Maintenir pour parler', '');
  };

  rec.onerror = (e) => {
    const msgs = {
      'not-allowed':   'Microphone refusé',
      'no-speech':     'Rien détecté',
      'network':       'Erreur réseau',
      'audio-capture': 'Aucun microphone',
    };
    addLog(msgs[e.error] || 'Erreur : ' + e.error, 'err');
    setMicStatus('Maintenir pour parler', '');
    micBtn.classList.remove('recording');
  };

  rec.onend = () => micBtn.classList.remove('recording');
  return rec;
}

micBtn.addEventListener('mousedown', (e) => {
  e.preventDefault();
  recognition = initRecognition();
  if (!recognition) return;
  try {
    recognition.start();
    micBtn.classList.add('recording');
    setMicStatus('🔴 En écoute…', 'listening');
    addLog('Écoute démarrée', 'info');
  } catch (err) { console.error(err); }
});

micBtn.addEventListener('mouseup', (e) => {
  e.preventDefault();
  if (recognition) { try { recognition.stop(); } catch {} }
  micBtn.classList.remove('recording');
  setMicStatus('Traitement…', 'processing');
});

micBtn.addEventListener('touchstart', (e) => {
  e.preventDefault();
  micBtn.dispatchEvent(new MouseEvent('mousedown'));
}, { passive: false });

micBtn.addEventListener('touchend', (e) => {
  e.preventDefault();
  micBtn.dispatchEvent(new MouseEvent('mouseup'));
}, { passive: false });

// ── UTILS ──
function setMicStatus(text, cls) {
  micStatus.textContent = text;
  micStatus.className   = 'mic-status' + (cls ? ' ' + cls : '');
}

function addLog(msg, type = '') {
  const container = document.getElementById('logEntries');
  const t = new Date().toTimeString().slice(0, 8);
  const d = document.createElement('div');
  d.className = 'log-entry';
  d.innerHTML = `<span class="log-time">${t}</span><span class="log-msg ${type}">${msg}</span>`;
  container.appendChild(d);
  container.scrollTop = container.scrollHeight;
}

document.getElementById('logClear').addEventListener('click', () => {
  document.getElementById('logEntries').innerHTML = '';
});

// ── SYNC ÉTAT INITIAL ──
fetch('/status').then(r => r.json()).then(d => {
  if (d.house_state) applyHouseState(d.house_state);
  addLog('Connecté au serveur', 'info');
}).catch(() => addLog('Serveur non joignable', 'err'));