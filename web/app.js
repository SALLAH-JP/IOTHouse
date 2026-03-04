// ===================================================
//  IOT House — app.js
// ===================================================

const state = {
  salon:         false,
  fan:           false,
  'garage-light':false,
  'garage-door': false,
  chambre:       false,
  cuisine:       false,
};

const roomWindows = {
  salon:          ['win-salon'],
  fan:            [],
  'garage-light': [],       // handled via garage-interior opacity
  'garage-door':  [],       // handled via panel animation
  chambre:        ['win-chambre'],
  cuisine:        ['win-cuisine'],
};

const windowClass = {
  salon:   'salon-on',
  chambre: 'chambre-on',
  cuisine: 'cuisine-on',
};

const commands = {
  salon:          { on: 'LED',   off: 'LED_OFF'   },
  fan:            { on: 'MOTOR', off: 'MOTOR_OFF' },
  'garage-light': { on: 'LED',   off: 'LED_OFF'   },
  'garage-door':  { on: 'MOTOR', off: 'MOTOR_OFF' },
  chambre:        { on: 'LED',   off: 'LED_OFF'   },
  cuisine:        { on: 'LED',   off: 'LED_OFF'   },
};

// ── TOGGLE ──
function toggleRoom(room) {
  state[room] = !state[room];
  const on = state[room];

  const cb = document.getElementById('toggle-' + room);
  if (cb) cb.checked = on;

  const card = document.getElementById('card-' + room);
  if (card) card.classList.toggle('active', on);

  // Fenêtres SVG lumières classiques
  (roomWindows[room] || []).forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('off', 'salon-on', 'chambre-on', 'cuisine-on', 'garage-on');
    el.classList.add(on && windowClass[room] ? windowClass[room] : 'off');
  });

  // Lumière garage (intérieur)
  if (room === 'garage-light') {
    const interior = document.getElementById('garage-interior');
    if (interior) interior.style.opacity = on ? '0.2' : '0';
  }

  // Porte garage
  if (room === 'garage-door') animateGarage(on);

  // Ventilateur
  if (room === 'fan') animateFan(on);

  sendCommand(on ? commands[room].on : commands[room].off, room, on);
}

// ── FAN ──
let fanSlowTimer = null;

function animateFan(on) {
  const group  = document.getElementById('fan-group');
  const blades = document.getElementById('fan-blades');
  if (!group || !blades) return;
  clearTimeout(fanSlowTimer);

  if (on) {
    group.style.opacity = '1';
    blades.classList.remove('slow');
    blades.classList.add('spinning');
  } else {
    blades.classList.remove('spinning');
    blades.classList.add('slow');
    fanSlowTimer = setTimeout(() => {
      blades.classList.remove('slow');
      group.style.opacity = '0.28';
    }, 1400);
  }
}

// ── GARAGE DOOR ──
function animateGarage(open) {
  const panels = [1,2,3,4].map(i => document.getElementById('garage-panel-' + i));

  if (open) {
    panels.forEach((p, i) => {
      if (!p) return;
      setTimeout(() => {
        p.style.transform = 'scaleY(0)';
        p.style.opacity   = '0';
      }, i * 100);
    });
  } else {
    panels.forEach((p, i) => {
      if (!p) return;
      setTimeout(() => {
        p.style.transform = 'scaleY(1)';
        p.style.opacity   = '1';
      }, i * 80);
    });
  }
}

// ── SEND COMMAND ──
async function sendCommand(cmd, room, on) {
  addLog(`${room.toUpperCase()} → ${cmd}`, 'cmd');
  try {
    const res = await fetch('/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    addLog('Arduino ✓', 'info');
  } catch {
    addLog('[demo] simulation locale', 'info');
  }
}

// ── EVENT LISTENERS ──
document.querySelectorAll('.room-card').forEach(card => {
  const room = card.dataset.room;
  card.addEventListener('click', e => {
    if (e.target.closest('.toggle')) return;
    toggleRoom(room);
  });
  const cb = document.getElementById('toggle-' + room);
  if (cb) cb.addEventListener('change', () => {
    if (cb.checked !== state[room]) toggleRoom(room);
  });
});

// ── MIC ──
let isRecording = false;
let recognition = null;

document.getElementById('micBtn').addEventListener('click', () => {
  isRecording ? stopRec() : startRec();
});

function startRec() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { addLog('Reconnaissance vocale non supportée', 'err'); return; }

  recognition = new SR();
  recognition.lang = 'fr-FR';
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    isRecording = true;
    document.getElementById('micBtn').classList.add('recording');
    const s = document.getElementById('micStatus');
    s.textContent = '🔴 En écoute…';
    s.className = 'mic-status listening';
    setTranscript('…');
    addLog('Écoute démarrée', 'info');
  };

  recognition.onresult = e => {
    let t = '';
    for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript;
    setTranscript(t);
  };

  recognition.onend = async () => {
    stopRec();
    const txt = document.getElementById('transcriptBox').textContent.trim();
    if (txt && txt !== '…' && txt !== 'En attente…') {
      addLog(`Voix : "${txt}"`, 'info');
      await sendVoice(txt);
    }
  };

  recognition.onerror = e => { addLog('Erreur micro : ' + e.error, 'err'); stopRec(); };
  recognition.start();
}

function stopRec() {
  isRecording = false;
  if (recognition) recognition.stop();
  document.getElementById('micBtn').classList.remove('recording');
  const s = document.getElementById('micStatus');
  s.textContent = 'Appuyez pour parler';
  s.className = 'mic-status';
}

async function sendVoice(text) {
  addLog("Envoi à l'assistant…", 'info');
  try {
    const res = await fetch('/voice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    if (data.type === 'commande') {
      addLog(`Commande IA : ${data.action}`, 'cmd');
    } else {
      addLog(`Réponse IA : ${data.reponse}`, 'info');
      setTranscript('💬 ' + data.reponse);
    }
  } catch {
    addLog('[demo] pas de backend connecté', 'info');
  }
}

// ── UTILS ──
function setTranscript(text) {
  const box = document.getElementById('transcriptBox');
  box.textContent = text;
  box.classList.toggle('active', text !== 'En attente…');
}

function addLog(msg, type = '') {
  const container = document.getElementById('logEntries');
  const time = new Date().toTimeString().slice(0, 8);
  const div  = document.createElement('div');
  div.className = 'log-entry';
  div.innerHTML = `<span class="log-time">${time}</span><span class="log-msg ${type}">${msg}</span>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

document.getElementById('logClear').addEventListener('click', () => {
  document.getElementById('logEntries').innerHTML = '';
});
