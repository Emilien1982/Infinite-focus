// Infinite Focus - Frontend JavaScript Application

let state = {
  isPlaying: false,
  isGenerating: false,
  status: 'initializing',
  audioLevel: 0.0,
  volume: 0.85,
  bufferedSeconds: 0,
  currentPrompt: '',
  device: 'Apple Silicon',
  presets: { curated: [], custom: [] }
};

const RANDOM_INSPIRATIONS = [
  "warm analog synthesizer drone, 432Hz deep meditative ambient soundscape, theta wave calm",
  "chill lofi hip hop beat, mellow electric rhodes chords, gentle vinyl crackle, cozy focus",
  "slow evolving ethereal ambient pads, crystal harmonics, deep concentration flow, peaceful",
  "minimalist modern classical piano, gentle rainy background, emotional focus chords",
  "deep space cosmic drone, hypnotic modular synth textures, celestial resonance, quiet mind",
  "zen temple acoustics, soft wooden bells, warm bamboo flute, tranquil meditation pad",
  "binaural alpha beats, gentle acoustic guitar harmonics, soft ambient haze, steady focus"
];

// DOM Elements
const playPauseBtn = document.getElementById('playPauseBtn');
const playIcon = document.getElementById('playIcon');
const pauseIcon = document.getElementById('pauseIcon');
const statusBadge = document.getElementById('statusBadge');
const statusText = document.getElementById('statusText');
const deviceText = document.getElementById('deviceText');
const detailStatus = document.getElementById('detailStatus');
const bufferInfo = document.getElementById('bufferInfo');
const promptInput = document.getElementById('promptInput');
const applyPromptBtn = document.getElementById('applyPromptBtn');
const randomPromptBtn = document.getElementById('randomPromptBtn');
const saveCurrentPromptBtn = document.getElementById('saveCurrentPromptBtn');
const curatedList = document.getElementById('curatedList');
const customList = document.getElementById('customList');
const customCount = document.getElementById('customCount');
const volumeSlider = document.getElementById('volumeSlider');
const volumePercent = document.getElementById('volumePercent');
const muteBtn = document.getElementById('muteBtn');
const canvas = document.getElementById('visualizerCanvas');
const ctx = canvas.getContext('2d');

let isMuted = false;
let previousVolume = 0.85;
let animationFrameId = null;
let wavePhase = 0;

// Setup canvas resolution
function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
}
window.addEventListener('resize', resizeCanvas);
setTimeout(resizeCanvas, 50);

// Visualizer animation loop
function drawVisualizer() {
  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;
  const centerY = height / 2;

  ctx.clearRect(0, 0, width, height);

  wavePhase += state.isPlaying ? 0.045 : 0.015;

  // Visualizer intensity based on playback level
  const baseAmp = state.isPlaying ? Math.max(12, state.audioLevel * 45) : 4;
  const lines = 3;

  for (let l = 0; l < lines; l++) {
    ctx.beginPath();
    const alpha = state.isPlaying ? 0.35 + (l * 0.2) : 0.15;
    const color = state.isGenerating
      ? `rgba(168, 85, 247, ${alpha})`
      : `rgba(6, 182, 212, ${alpha})`;

    ctx.strokeStyle = color;
    ctx.lineWidth = l === lines - 1 ? 2.5 : 1.5;

    for (let x = 0; x <= width; x += 4) {
      const progress = x / width;
      // Window envelope to fade out edges
      const envelope = Math.sin(progress * Math.PI);
      const freq = 0.012 + (l * 0.005);
      const y = centerY + Math.sin(x * freq + wavePhase + (l * 1.2)) * baseAmp * envelope;

      if (x === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
  }

  animationFrameId = requestAnimationFrame(drawVisualizer);
}
drawVisualizer();

// Initialize communication with Python backend
window.addEventListener('pywebviewready', async () => {
  console.log("pywebview API ready!");
  await loadPresets();
  await refreshState();
  setInterval(refreshState, 150);
});

async function refreshState() {
  if (!window.pywebview || !window.pywebview.api) return;

  try {
    const s = await window.pywebview.api.get_state();
    state.isPlaying = s.is_playing;
    state.isGenerating = s.is_generating;
    state.status = s.status;
    state.audioLevel = s.audio_level;
    state.volume = s.volume;
    state.bufferedSeconds = s.buffered_seconds;
    state.device = s.device;

    updateUI(s);
  } catch (err) {
    console.error("Error refreshing state:", err);
  }
}

function updateUI(s) {
  // Update Play / Pause Button
  if (state.isPlaying) {
    playIcon.classList.add('hidden');
    pauseIcon.classList.remove('hidden');
  } else {
    playIcon.classList.remove('hidden');
    pauseIcon.classList.add('hidden');
  }

  // Update Status Badge
  statusBadge.className = 'status-badge';
  if (s.is_generating) {
    statusBadge.classList.add('generating');
    statusText.textContent = "Génération IA en RAM...";
  } else if (s.is_playing) {
    statusBadge.classList.add('playing');
    statusText.textContent = "Lecture continue";
  } else if (s.status === 'paused') {
    statusBadge.classList.add('paused');
    statusText.textContent = "En pause";
  } else if (s.status === 'ready') {
    statusBadge.classList.add('ready');
    statusText.textContent = "Prêt";
  } else {
    statusBadge.classList.add('initializing');
    statusText.textContent = s.status_detail || "Initialisation...";
  }

  detailStatus.textContent = s.status_detail || "Prêt";
  
  const bufSec = Math.round(s.buffered_seconds || 0);
  if (bufSec >= 60) {
    const mins = Math.floor(bufSec / 60);
    const secs = bufSec % 60;
    bufferInfo.textContent = `Flux RAM: ${mins}m ${secs}s`;
  } else {
    bufferInfo.textContent = `Flux RAM: ${bufSec}s`;
  }

  if (s.is_generating && s.buffered_seconds === 0) {
    playPauseBtn.classList.add('loading-pulse');
  } else {
    playPauseBtn.classList.remove('loading-pulse');
  }

  deviceText.textContent = `${s.device} (MPS)`;

  // Keep prompt input updated if user hasn't typed
  if (!promptInput.value && s.current_prompt) {
    promptInput.value = s.current_prompt;
  }
}

async function loadPresets() {
  if (!window.pywebview || !window.pywebview.api) return;
  try {
    const data = await window.pywebview.api.get_presets();
    state.presets = data;
    renderPresets();
  } catch (err) {
    console.error("Error loading presets:", err);
  }
}

function renderPresets() {
  // Render Curated
  curatedList.innerHTML = '';
  state.presets.curated.forEach(preset => {
    const card = document.createElement('div');
    card.className = 'preset-card';
    card.innerHTML = `
      <div class="preset-header">
        <div class="preset-title-wrap">
          <span class="preset-icon">${preset.icon || '🎵'}</span>
          <span class="preset-title">${preset.name}</span>
        </div>
        <span class="preset-cat">${preset.category || 'Focus'}</span>
      </div>
      <div class="preset-prompt-preview">${preset.prompt}</div>
    `;
    card.addEventListener('click', () => {
      promptInput.value = preset.prompt;
      highlightActiveCard(card);
      triggerPlay(preset.prompt);
    });
    curatedList.appendChild(card);
  });

  // Render Custom
  customList.innerHTML = '';
  customCount.textContent = state.presets.custom.length;

  if (state.presets.custom.length === 0) {
    customList.innerHTML = `
      <div class="empty-state">
        <p>Aucun prompt personnalisé sauvegardé.</p>
        <p class="empty-hint">Tapez votre prompt ci-dessus et cliquez sur "⭐ Sauvegarder".</p>
      </div>
    `;
  } else {
    state.presets.custom.forEach(preset => {
      const card = document.createElement('div');
      card.className = 'preset-card';
      card.innerHTML = `
        <div class="preset-header">
          <div class="preset-title-wrap">
            <span class="preset-icon">${preset.icon || '✨'}</span>
            <span class="preset-title">${preset.name}</span>
          </div>
          <button class="btn-delete-preset" title="Supprimer ce preset">✕</button>
        </div>
        <div class="preset-prompt-preview">${preset.prompt}</div>
      `;
      card.querySelector('.btn-delete-preset').addEventListener('click', async (e) => {
        e.stopPropagation();
        await deletePreset(preset.id);
      });
      card.addEventListener('click', () => {
        promptInput.value = preset.prompt;
        highlightActiveCard(card);
        triggerPlay(preset.prompt);
      });
      customList.appendChild(card);
    });
  }
}

function highlightActiveCard(cardElement) {
  document.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active-preset'));
  cardElement.classList.add('active-preset');
}

// User Actions
async function triggerPlay(customPrompt = null) {
  const p = customPrompt || promptInput.value.trim();
  if (!p) {
    alert("Veuillez renseigner un prompt sonore.");
    return;
  }
  if (!window.pywebview || !window.pywebview.api) return;

  try {
    await window.pywebview.api.play(p);
    state.isPlaying = true;
    await refreshState();
  } catch (err) {
    console.error("Error triggering play:", err);
  }
}

playPauseBtn.addEventListener('click', async () => {
  if (!window.pywebview || !window.pywebview.api) return;
  const p = promptInput.value.trim();
  try {
    const res = await window.pywebview.api.toggle_play(p);
    state.isPlaying = res;
    await refreshState();
  } catch (err) {
    console.error("Error toggling play:", err);
  }
});

applyPromptBtn.addEventListener('click', async () => {
  const p = promptInput.value.trim();
  if (!p || !window.pywebview || !window.pywebview.api) return;
  try {
    statusBadge.className = 'status-badge generating';
    statusText.textContent = "Génération nouveau thème...";
    detailStatus.textContent = "Changement de thème : composition immédiate du nouveau morceau...";
    await window.pywebview.api.set_prompt(p);
    await refreshState();
  } catch (err) {
    console.error("Error setting prompt:", err);
  }
});

randomPromptBtn.addEventListener('click', () => {
  const randomChoice = RANDOM_INSPIRATIONS[Math.floor(Math.random() * RANDOM_INSPIRATIONS.length)];
  promptInput.value = randomChoice;
  promptInput.focus();
});

saveCurrentPromptBtn.addEventListener('click', async () => {
  const p = promptInput.value.trim();
  if (!p) {
    alert("Veuillez écrire un prompt à sauvegarder.");
    return;
  }
  const name = prompt("Nom du préréglage :", "Mon Focus " + new Date().toLocaleDateString('fr-FR'));
  if (name && name.trim()) {
    try {
      const res = await window.pywebview.api.save_preset(name.trim(), p);
      if (res && res.presets) {
        state.presets = res.presets;
        renderPresets();
        // Switch to custom tab to view the newly saved preset
        document.querySelector('.tab-btn[data-tab="custom"]').click();
      }
    } catch (err) {
      console.error("Error saving preset:", err);
    }
  }
});

async function deletePreset(id) {
  if (!confirm("Voulez-vous supprimer ce préréglage sauvegardé ?")) return;
  try {
    const res = await window.pywebview.api.delete_preset(id);
    if (res && res.presets) {
      state.presets = res.presets;
      renderPresets();
    }
  } catch (err) {
    console.error("Error deleting preset:", err);
  }
}

// Volume Controls
volumeSlider.addEventListener('input', (e) => {
  const val = parseInt(e.target.value) / 100.0;
  volumePercent.textContent = `${Math.round(val * 100)}%`;
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.set_volume(val);
  }
  isMuted = val === 0;
});

muteBtn.addEventListener('click', () => {
  if (isMuted) {
    isMuted = false;
    volumeSlider.value = Math.round(previousVolume * 100);
    volumePercent.textContent = `${Math.round(previousVolume * 100)}%`;
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.set_volume(previousVolume);
    }
  } else {
    previousVolume = parseInt(volumeSlider.value) / 100.0;
    isMuted = true;
    volumeSlider.value = 0;
    volumePercent.textContent = "0%";
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.set_volume(0.0);
    }
  }
});

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    btn.classList.add('active');
    const tabId = `${btn.dataset.tab}Tab`;
    const target = document.getElementById(tabId);
    if (target) target.classList.add('active');
  });
});
