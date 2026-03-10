// ===================================================
//  IOT House — app.js
// ===================================================

const state = {
  salon:          false,
  fan:            false,
  'garage-light': false,
  'garage-door':  false,
  chambre:        false,
  cuisine:        false,
};

const roomWindows = {
  salon:          ['win-salon'],
  fan:            [],
  'garage-light': [],
  'garage-door':  [],
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
  applyState(room);
  sendCommand(state[room] ? commands[room].on : commands[room].off, room, state[room]);
}

function setRoom(room, on) {
  if (state[room] === on) return;
  state[room] = on;
  applyState(room);
  sendCommand(on ? commands[room].on : commands[room].off, room, on);
}

function applyState(room) {
  const on   = state[room];
  const cb   = document.getElementById('toggle-' + room);
  const card = document.getElementById('card-' + room);
  if (cb)   cb.checked = on;
  if (card) card.classList.toggle('active', on);

  (roomWindows[room] || []).forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('off', 'salon-on', 'chambre-on', 'cuisine-on', 'garage-on');
    el.classList.add(on && windowClass[room] ? windowClass[room] : 'off');
  });

  if (room === 'garage-light') {
    const interior = document.getElementById('garage-interior');
    if (interior) interior.style.opacity = on ? '0.22' : '0';
  }
  if (room === 'garage-door') animateGarage(on);
  if (room === 'fan')         animateFan(on);
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
      group.style.opacity = '0.35';
    }, 1400);
  }
}

// ── GARAGE ──
function animateGarage(open) {
  const panels = [1,2,3,4].map(i => document.getElementById('garage-panel-' + i));
  if (open) {
    panels.forEach((p, i) => {
      if (!p) return;
      setTimeout(() => { p.style.transform = 'scaleY(0)'; p.style.opacity = '0'; }, i * 100);
    });
  } else {
    panels.forEach((p, i) => {
      if (!p) return;
      setTimeout(() => { p.style.transform = 'scaleY(1)'; p.style.opacity = '1'; }, i * 80);
    });
  }
}

// ── SEND COMMAND TO ARDUINO ──
async function sendCommand(cmd, room, on) {
  addLog(`${room.toUpperCase()} → ${cmd}`, 'cmd');
  try {
    const res = await fetch('/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd, room, on }),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    addLog('Arduino ✓', 'info');
  } catch {
    addLog('[démo] simulation locale', 'info');
  }
}

// ── APPLY OLLAMA ACTIONS ON UI ──
function applyOllamaAction(action, parametres) {
  const p = parametres || {};
  const pieceMap = {
    salon:   'salon',
    chambre: 'chambre',
    cuisine: 'cuisine',
    garage:  'garage-light',
  };

  const piece = p.pièce || p.piece || p.room || null;
  const room  = pieceMap[piece] || null;

  if (action === 'allumerLed') {
    if (room) setRoom(room, true);
    else ['salon','chambre','cuisine','garage-light'].forEach(r => setRoom(r, true));
  } else if (action === 'eteindreLed') {
    if (room) setRoom(room, false);
    else ['salon','chambre','cuisine','garage-light'].forEach(r => setRoom(r, false));
  } else if (action === 'allumerMoteur') {
    setRoom('fan', true);
  } else if (action === 'eteindreMoteur') {
    setRoom('fan', false);
  } else if (action === 'ouvrirGarage') {
    setRoom('garage-door', true);
  } else if (action === 'fermerGarage') {
    setRoom('garage-door', false);
  }
}

// ── PUSH-TO-TALK ──
let recognition = null;
let finalTranscript = '';

const micBtn       = document.getElementById('micBtn');
const transcriptBox = document.getElementById('transcriptBox');
const micStatus    = document.getElementById('micStatus');
const userTextEl   = document.getElementById('userText');
const aiReplyEl    = document.getElementById('aiReply');

// Initialise Web Speech API
function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    addLog('Web Speech API non supportée', 'err');
    return null;
  }
  const rec = new SR();
  rec.continuous      = false;
  rec.interimResults  = false;
  rec.lang            = 'fr-FR';

  rec.onresult = async (event) => {
    const transcript = event.results[0][0].transcript.trim();
    console.log('[STT] transcript:', transcript);
    
    document.getElementById('userText').textContent = transcript;
    setMicStatus('Traitement…', 'processing');
    addLog(`Voix : "${transcript}"`, 'info');

    try {
      const res = await fetch('/send_text', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ user_text: transcript }),
      });
      const data = await res.json();
      console.log('[Backend] réponse:', data);

      document.getElementById('aiReply').textContent = data.ai_reply || '';
      if (data.action) applyOllamaAction(data.action, data.parametres);
      if (data.tts_url) new Audio(data.tts_url).play().catch(console.error);
      addLog(`IA : ${(data.ai_reply || '').slice(0, 80)}`, 'info');

    } catch(e) {
      console.error('[Backend] erreur:', e);
      addLog('Erreur backend : ' + e.message, 'err');
    }

    setMicStatus('Maintenir pour parler', '');
  };

  rec.onerror = (e) => {
    console.error('[STT] erreur:', e.error);
    addLog('Erreur micro : ' + e.error, 'err');
    setMicStatus('Maintenir pour parler', '');
    micBtn.classList.remove('recording');
  };

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
  } catch(err) {
    console.error(err);
  }
});

micBtn.addEventListener('mouseup', (e) => {
  e.preventDefault();
  if (recognition) {
    try { recognition.stop(); } catch {}
  }
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


// ── EVENT LISTENERS BOUTONS ──
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

// ── UTILS ──
function setMicStatus(text, cls) {
  micStatus.textContent = text;
  micStatus.className   = 'mic-status' + (cls ? ' ' + cls : '');
}

function setTranscript(text) {
  transcriptBox.classList.toggle('active', text !== 'En attente…' && text !== '…');
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
