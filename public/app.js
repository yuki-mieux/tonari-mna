/**
 * 聖人君子AI - フロントエンド
 * 管理職の1on1・会議をリアルタイムで支援し、パワハラを未然に防ぐ
 */

// ===== Configuration =====
const SUPABASE_URL = 'https://znvfqvyhwnmwzyjkiedq.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpudmZxdnlod25td3p5amtpZWRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU2MDMzNDQsImV4cCI6MjA4MTE3OTM0NH0.VDUGYVmsJWgpGPzvgDOW-xNxIGdi9UF3nfaj8Q5loKw';

const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
const isProduction = !['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_URL = isProduction ? '' : 'http://localhost:8000';

// ===== State =====
let currentUser = null;
let DEEPGRAM_API_KEY = '';
let isRecording = false;
let conversationBuffer = [];
let riskEvents = [];
let selfWordCount = 0;
let otherWordCount = 0;

// Recording state
let micSocket = null;
let displaySocket = null;
let micRecorder = null;
let displayRecorder = null;
let micStream = null;
let displayStream = null;
let intentionalStop = false;
let selectedMicId = localStorage.getItem('seijin_mic_id') || '';

// ===== DOM Elements =====
const $ = id => document.getElementById(id);
const playBtn = $('playBtn');
const playIcon = $('playIcon');
const stopIcon = $('stopIcon');
const statusText = $('statusText');
const transcriptLog = $('transcriptLog');
const cardsArea = $('cardsArea');
const emptyState = $('emptyState');
const balanceFill = $('balanceFill');
const sessionEndBtn = $('sessionEndBtn');
const settingsModal = $('settingsModal');
const reflectionModal = $('reflectionModal');
const micSelect = $('micSelect');

// ===== Auth =====
async function checkAuth() {
  // Skip auth for local development
  if (!isProduction) {
    currentUser = { email: 'dev@localhost' };
    showApp();
    return;
  }
  const { data: { session } } = await supabaseClient.auth.getSession();
  if (session) {
    currentUser = session.user;
    showApp();
  } else {
    showAuthScreen();
  }
}

function showAuthScreen() {
  $('authScreen').classList.remove('hidden');
  $('appContainer').style.display = 'none';
}

async function showApp() {
  $('authScreen').classList.add('hidden');
  $('appContainer').style.display = 'block';
  if (currentUser) $('userEmail').textContent = currentUser.email;
  $('logoutBtn').onclick = logout;
  await loadConfig();
}

async function loadConfig() {
  try {
    const res = await apiFetch(`${API_URL}/api/config`);
    if (res.ok) {
      const data = await res.json();
      DEEPGRAM_API_KEY = data.deepgram_api_key || '';
    }
  } catch (e) {
    console.error('Failed to load config:', e);
  }
}

function showAuthError(message) {
  const el = $('authError');
  el.textContent = message;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 5000);
}

$('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = $('loginEmail').value;
  const password = $('loginPassword').value;
  const btn = $('loginBtn');
  btn.disabled = true;
  btn.textContent = 'ログイン中...';
  try {
    const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
    if (error) throw error;
    currentUser = data.user;
    showApp();
  } catch (error) {
    showAuthError(error.message || 'ログインに失敗しました');
  } finally {
    btn.disabled = false;
    btn.textContent = 'ログイン';
  }
});

async function logout() {
  await supabaseClient.auth.signOut();
  currentUser = null;
  showAuthScreen();
}

supabaseClient.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN' && session) {
    currentUser = session.user;
    showApp();
  } else if (event === 'SIGNED_OUT') {
    currentUser = null;
    showAuthScreen();
  }
});

// ===== API Helper =====
async function getApiHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const { data: { session } } = await supabaseClient.auth.getSession();
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }
  return headers;
}

async function apiFetch(url, options = {}) {
  const headers = await getApiHeaders();
  return fetch(url, { ...options, headers: { ...options.headers, ...headers } });
}

// ===== Settings Modal =====
$('settingsBtn').onclick = () => {
  settingsModal.classList.add('show');
  loadMicrophones();
};
$('closeSettings').onclick = () => settingsModal.classList.remove('show');
settingsModal.onclick = (e) => { if (e.target === settingsModal) settingsModal.classList.remove('show'); };

async function loadMicrophones() {
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
    const devices = await navigator.mediaDevices.enumerateDevices();
    const mics = devices.filter(d => d.kind === 'audioinput');
    micSelect.innerHTML = '<option value="">デフォルト</option>';
    mics.forEach(mic => {
      const option = document.createElement('option');
      option.value = mic.deviceId;
      option.textContent = mic.label || `マイク ${mic.deviceId.slice(0, 8)}`;
      if (mic.deviceId === selectedMicId) option.selected = true;
      micSelect.appendChild(option);
    });
  } catch (e) {
    console.error('マイク一覧取得エラー:', e);
  }
}

$('refreshMics').onclick = loadMicrophones;
$('saveSettings').onclick = () => {
  selectedMicId = micSelect.value;
  localStorage.setItem('seijin_mic_id', selectedMicId);
  settingsModal.classList.remove('show');
};

// ===== Reflection Modal =====
$('closeReflection').onclick = () => reflectionModal.classList.remove('show');
reflectionModal.onclick = (e) => { if (e.target === reflectionModal) reflectionModal.classList.remove('show'); };

// ===== Recording =====
playBtn.onclick = () => isRecording ? stopRecording() : startRecording();

async function startRecording() {
  intentionalStop = false;
  if (!DEEPGRAM_API_KEY) {
    alert('音声認識の設定が完了していません。');
    return;
  }

  try {
    // Get microphone stream
    const audioConstraints = selectedMicId ? { deviceId: { exact: selectedMicId } } : true;
    micStream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
    console.log('[聖人君子AI] Mic stream acquired');

    // Get display stream (for remote audio)
    try {
      displayStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      displayStream.getVideoTracks().forEach(track => track.stop());
      console.log('[聖人君子AI] Display stream acquired');
    } catch (e) {
      console.log('[聖人君子AI] Display share cancelled:', e.message);
      displayStream = null;
    }

    // Reset state
    resetSession();

    // Create Deepgram sockets
    micSocket = createDeepgramSocket('self');
    micSocket.onopen = () => {
      console.log('[聖人君子AI] Mic socket opened');
      updateUI(true);
      micRecorder = new MediaRecorder(micStream, { mimeType: 'audio/webm;codecs=opus' });
      micRecorder.ondataavailable = (e) => {
        if (e.data.size > 0 && micSocket.readyState === WebSocket.OPEN) {
          micSocket.send(e.data);
        }
      };
      micRecorder.start(250);
    };

    if (displayStream?.getAudioTracks().length > 0) {
      displaySocket = createDeepgramSocket('other');
      displaySocket.onopen = () => {
        console.log('[聖人君子AI] Display socket opened');
        displayRecorder = new MediaRecorder(displayStream, { mimeType: 'audio/webm;codecs=opus' });
        displayRecorder.ondataavailable = (e) => {
          if (e.data.size > 0 && displaySocket.readyState === WebSocket.OPEN) {
            displaySocket.send(e.data);
          }
        };
        displayRecorder.start(250);
      };
    }
  } catch (e) {
    alert('エラー: ' + e.message);
  }
}

function createDeepgramSocket(speaker) {
  const socket = new WebSocket(
    'wss://api.deepgram.com/v1/listen?' + new URLSearchParams({
      model: 'nova-3', language: 'ja', punctuate: 'true',
      interim_results: 'true', endpointing: '300', smart_format: 'true'
    }),
    ['token', DEEPGRAM_API_KEY]
  );

  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    const transcript = data.channel?.alternatives?.[0]?.transcript
      || data.results?.channels?.[0]?.alternatives?.[0]?.transcript;
    const isFinal = data.is_final ?? data.results?.is_final ?? false;

    if (transcript) {
      console.log(`[聖人君子AI] ${speaker}: "${transcript}" (final: ${isFinal})`);
      addTranscript(transcript, isFinal, speaker);
    }
  };

  socket.onerror = (e) => console.log(`[聖人君子AI] ${speaker} socket error:`, e);
  socket.onclose = () => {
    console.log(`[聖人君子AI] ${speaker} socket closed`);
    if (!intentionalStop && speaker === 'self') updateUI(false);
  };

  return socket;
}

function stopRecording() {
  intentionalStop = true;
  if (micRecorder?.state !== 'inactive') micRecorder?.stop();
  if (displayRecorder?.state !== 'inactive') displayRecorder?.stop();
  micSocket?.close();
  displaySocket?.close();
  micSocket = displaySocket = micRecorder = displayRecorder = null;
  micStream?.getTracks().forEach(t => t.stop());
  displayStream?.getTracks().forEach(t => t.stop());
  micStream = displayStream = null;
  updateUI(false);
}

function resetSession() {
  conversationBuffer = [];
  riskEvents = [];
  selfWordCount = 0;
  otherWordCount = 0;
  transcriptLog.innerHTML = '';
  cardsArea.innerHTML = '';
  cardsArea.appendChild(emptyState);
  emptyState.style.display = 'flex';
  sessionEndBtn.style.display = 'none';
  updateBalanceBar();
}

function updateUI(recording) {
  isRecording = recording;
  playBtn.classList.toggle('recording', recording);
  playIcon.style.display = recording ? 'none' : 'block';
  stopIcon.style.display = recording ? 'block' : 'none';
  statusText.textContent = recording ? '録音中' : '待機中';
  statusText.classList.toggle('recording', recording);
  if (recording) {
    sessionEndBtn.style.display = 'block';
  }
}

// ===== Transcript =====
const speakerLabels = { self: '自分', other: '相手' };
let lastTranscriptItem = null;
let lastTranscriptSpeaker = null;

function addTranscript(text, isFinal, speaker = 'self') {
  text = text.replace(/[\r\n]+/g, ' ').trim();
  if (!text) return;

  // Remove interim
  const existing = transcriptLog.querySelector(`.transcript-item.interim[data-speaker="${speaker}"]`);
  if (existing) existing.remove();

  const time = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  // Append to existing block if same speaker
  const canAppend = isFinal && lastTranscriptItem && lastTranscriptSpeaker === speaker && !lastTranscriptItem.classList.contains('interim');

  if (canAppend) {
    const textDiv = lastTranscriptItem.querySelector('.transcript-text');
    if (textDiv) textDiv.innerHTML += ` ${text}`;
  } else {
    const item = document.createElement('div');
    item.className = `transcript-item ${speaker}` + (isFinal ? '' : ' interim');
    item.setAttribute('data-speaker', speaker);
    item.innerHTML = `
      <div class="transcript-meta">
        <span class="transcript-speaker ${speaker}">${speakerLabels[speaker]}</span>
        <span class="transcript-time">${time}</span>
      </div>
      <div class="transcript-text">${text}</div>
    `;
    transcriptLog.appendChild(item);
    if (isFinal) {
      lastTranscriptItem = item;
      lastTranscriptSpeaker = speaker;
    }
  }
  transcriptLog.scrollTop = transcriptLog.scrollHeight;

  if (isFinal && text.length > 5) {
    // Update word count for balance
    const wordCount = text.length;
    if (speaker === 'self') selfWordCount += wordCount;
    else otherWordCount += wordCount;
    updateBalanceBar();

    // Add to buffer and request analysis
    conversationBuffer.push({ time, text, speaker });
    if (conversationBuffer.length > 30) conversationBuffer.shift();
    requestHarassmentCheck();
  }
}

function updateBalanceBar() {
  const total = selfWordCount + otherWordCount;
  const selfPercent = total > 0 ? (selfWordCount / total) * 100 : 50;
  balanceFill.style.width = `${selfPercent}%`;
}

// ===== AI Harassment Check =====
let checkDebounce = null;

async function requestHarassmentCheck() {
  if (conversationBuffer.length < 2) return;
  if (checkDebounce) return;
  checkDebounce = setTimeout(() => { checkDebounce = null; }, 10000); // 10秒間隔

  try {
    const transcript = conversationBuffer
      .map(c => `${c.time} [${speakerLabels[c.speaker]}]: ${c.text}`)
      .join('\n');

    console.log('[聖人君子AI] Checking harassment...');
    const res = await apiFetch(`${API_URL}/api/harassment_check`, {
      method: 'POST',
      body: JSON.stringify({ transcript })
    });

    if (res.ok) {
      const data = await res.json();
      console.log('[聖人君子AI] Check result:', data);
      if (data.risk_detected && data.risk_level !== 'none') {
        addRiskCard(data);
      }
    }
  } catch (e) {
    console.error('[聖人君子AI] Check error:', e);
  }
}

function addRiskCard(data) {
  // Hide empty state
  emptyState.style.display = 'none';

  // Mark existing cards as past
  cardsArea.querySelectorAll('.risk-card:not(.past)').forEach(card => {
    card.classList.add('past');
  });

  const levelLabel = data.risk_level === 'high' ? '高リスク' : '中リスク';
  const time = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

  const card = document.createElement('div');
  card.className = `risk-card ${data.risk_level}`;
  card.innerHTML = `
    <div class="risk-card-header">
      <span class="risk-level ${data.risk_level}">${levelLabel}</span>
      <span class="risk-time">${time}</span>
    </div>
    <div class="risk-card-body">
      <div class="risk-quote">「${data.detected_text}」</div>
      <div class="risk-analysis">${data.analysis}</div>
      <div class="rephrase-section">
        <div class="rephrase-label">💡 こう言い換えては？</div>
        <div class="rephrase-text">「${data.rephrase}」</div>
      </div>
    </div>
  `;

  // Insert at top
  cardsArea.insertBefore(card, cardsArea.firstChild);

  // Store for reflection
  riskEvents.push({
    time,
    text: data.detected_text,
    risk_level: data.risk_level,
    analysis: data.analysis,
    rephrase: data.rephrase
  });
}

// ===== Session End & Reflection =====
sessionEndBtn.onclick = async () => {
  stopRecording();
  await showReflection();
};

async function showReflection() {
  const content = $('reflectionContent');
  content.innerHTML = '<div class="empty-state"><div class="empty-text">振り返りを生成中...</div></div>';
  reflectionModal.classList.add('show');

  try {
    const transcript = conversationBuffer
      .map(c => `${c.time} [${speakerLabels[c.speaker]}]: ${c.text}`)
      .join('\n');

    const res = await apiFetch(`${API_URL}/api/reflection`, {
      method: 'POST',
      body: JSON.stringify({ transcript, risk_events: riskEvents })
    });

    if (res.ok) {
      const data = await res.json();
      renderReflection(data);
    } else {
      content.innerHTML = '<div class="empty-state"><div class="empty-text">振り返りの生成に失敗しました</div></div>';
    }
  } catch (e) {
    console.error('[聖人君子AI] Reflection error:', e);
    content.innerHTML = '<div class="empty-state"><div class="empty-text">エラーが発生しました</div></div>';
  }
}

function renderReflection(data) {
  const content = $('reflectionContent');
  content.innerHTML = `
    <div class="reflection-section">
      <div class="reflection-title">📝 会話サマリー</div>
      <div class="reflection-summary">${data.summary}</div>
    </div>

    <div class="reflection-section">
      <div class="reflection-title">👍 良かった点</div>
      ${data.positive_points.map(p => `
        <div class="feedback-item positive">
          <div class="feedback-icon positive">✓</div>
          <div class="feedback-text">${p}</div>
        </div>
      `).join('')}
    </div>

    <div class="reflection-section">
      <div class="reflection-title">💡 改善できる点</div>
      ${data.improvement_points.map(p => `
        <div class="feedback-item improvement">
          <div class="feedback-icon improvement">!</div>
          <div class="feedback-text">${p}</div>
        </div>
      `).join('')}
    </div>

    <div class="reflection-section">
      <div class="reflection-title">📋 次回へのアクション</div>
      ${data.next_actions.map(a => `
        <div class="action-item">
          <div class="action-checkbox"></div>
          <div>${a}</div>
        </div>
      `).join('')}
    </div>
  `;
}

// ===== Initialize =====
checkAuth();
