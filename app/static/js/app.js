/* KaraokePro - Main Application Logic */

const API = {
    async get(url) {
        const res = await fetch(url);
        return res.json();
    },
    async post(url, data = {}) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async del(url) {
        const res = await fetch(url, { method: 'DELETE' });
        return res.json();
    }
};

// ---- State ----
let state = {
    sessionActive: false,
    sessionId: null,
    queue: [],
    current: null,
    selectedSong: null,
    selectedTip: 0,
    stats: {},
};

// ---- Init ----
document.addEventListener('DOMContentLoaded', async () => {
    await checkSession();
    setupEventListeners();
    // Poll for updates every 3 seconds
    setInterval(refreshQueue, 3000);
});

async function checkSession() {
    const data = await API.get('/api/session/current');
    state.sessionActive = data.active;
    state.sessionId = data.session_id || null;
    state.stats = data.stats || {};
    if (data.active) {
        await refreshQueue();
    }
    renderAll();
}

// ---- Session ----
async function startSession() {
    const data = await API.post('/api/session/start');
    state.sessionActive = true;
    state.sessionId = data.session_id;
    state.queue = [];
    state.current = null;
    renderAll();
    showToast('Session started!');
}

async function endSession() {
    if (!confirm('End the current session? This will clear the queue.')) return;
    const data = await API.post('/api/session/end');
    state.sessionActive = false;
    state.sessionId = null;
    state.queue = [];
    state.current = null;
    state.stats = data.stats || {};
    renderAll();
    showToast('Session ended');
}

// ---- Queue ----
async function refreshQueue() {
    if (!state.sessionActive) return;
    const data = await API.get('/api/queue');
    state.queue = data.queue;
    state.current = data.current;
    renderQueue();
    renderNowSinging();
    await refreshStats();
}

async function refreshStats() {
    if (!state.sessionActive) return;
    const data = await API.get('/api/session/current');
    state.stats = data.stats || {};
    renderStats();
}

async function addSinger() {
    const nameInput = document.getElementById('singer-name');
    const name = nameInput.value.trim();
    if (!name) { nameInput.focus(); return; }
    if (!state.selectedSong) { showToast('Select a song first'); return; }

    const data = await API.post('/api/queue/add', {
        name: name,
        song_title: state.selectedSong.title,
        song_artist: state.selectedSong.artist,
        file_path: state.selectedSong.file_path || '',
        tip_amount: state.selectedTip,
    });

    if (data.error) {
        showToast(data.error);
        return;
    }

    state.queue = data.queue;
    // Reset form
    nameInput.value = '';
    document.getElementById('song-search').value = '';
    document.getElementById('search-results').innerHTML = '';
    document.getElementById('selected-song').style.display = 'none';
    state.selectedSong = null;
    state.selectedTip = 0;
    renderTipButtons();
    renderQueue();
    showToast(`${name} added to queue`);
    nameInput.focus();
}

async function nextSinger() {
    const data = await API.post('/api/queue/next');
    state.current = data.current;
    state.queue = data.queue;
    renderAll();
    if (state.current) {
        showToast(`Up now: ${state.current.name}`);
    }
}

async function removeSinger(position) {
    if (!confirm('Remove this singer?')) return;
    const data = await API.del(`/api/queue/${position}`);
    state.queue = data.queue;
    renderQueue();
}

async function moveToTop(position) {
    const data = await API.post(`/api/queue/${position}/top`);
    state.queue = data.queue;
    renderQueue();
}

async function addQueueTip(position) {
    const amount = prompt('Tip amount ($):');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) return;
    const data = await API.post(`/api/queue/${position}/tip`, { amount: parseFloat(amount) });
    if (data.queue) {
        state.queue = data.queue;
        renderQueue();
        showToast(data.message);
    }
}

// ---- Song Search ----
let searchTimeout = null;

function setupSongSearch() {
    const input = document.getElementById('song-search');
    if (!input) return;

    input.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const query = input.value.trim();
        if (query.length < 2) {
            document.getElementById('search-results').innerHTML = '';
            return;
        }
        searchTimeout = setTimeout(() => searchSongs(query), 200);
    });
}

async function searchSongs(query) {
    const results = await API.get(`/api/songs/search?q=${encodeURIComponent(query)}`);
    renderSearchResults(results);
}

function selectSong(song) {
    state.selectedSong = song;
    document.getElementById('search-results').innerHTML = '';
    document.getElementById('song-search').value = '';

    const el = document.getElementById('selected-song');
    el.style.display = 'block';
    el.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
                <div style="font-weight:600">${esc(song.title)}</div>
                <div style="color:var(--text-secondary);font-size:0.85rem">${esc(song.artist)}</div>
            </div>
            <button class="btn-icon" onclick="clearSong()" title="Clear">&times;</button>
        </div>
    `;
}

function clearSong() {
    state.selectedSong = null;
    document.getElementById('selected-song').style.display = 'none';
    document.getElementById('song-search').value = '';
    document.getElementById('song-search').focus();
}

// ---- Tip Selection ----
function selectTip(amount) {
    state.selectedTip = amount;
    renderTipButtons();
}

function customTip() {
    const val = prompt('Custom tip amount ($):');
    if (val && !isNaN(val) && parseFloat(val) > 0) {
        state.selectedTip = parseFloat(val);
        renderTipButtons();
    }
}

// ---- Render Functions ----
function renderAll() {
    renderSessionBar();
    renderNowSinging();
    renderQueue();
    renderStats();
    renderTipButtons();
}

function renderSessionBar() {
    const bar = document.getElementById('session-bar');
    if (!bar) return;

    if (state.sessionActive) {
        bar.className = 'session-bar';
        bar.innerHTML = `
            <span style="color:var(--green);font-weight:600">SESSION ACTIVE</span>
            <button class="btn btn-danger btn-small" onclick="endSession()">End Session</button>
        `;
    } else {
        bar.className = 'session-bar inactive';
        bar.innerHTML = `
            <span style="color:var(--red)">No active session</span>
            <button class="btn btn-success" onclick="startSession()">Start Session</button>
        `;
    }
}

function renderNowSinging() {
    const el = document.getElementById('now-singing');
    if (!el) return;

    if (state.current) {
        el.className = 'now-singing';
        el.innerHTML = `
            <div class="label">NOW SINGING</div>
            <div class="singer-name">${esc(state.current.name)}</div>
            <div class="song-info">${esc(state.current.song_title)} — ${esc(state.current.song_artist)}</div>
            <button class="btn-next" onclick="nextSinger()">SONG DONE — NEXT SINGER</button>
        `;
    } else {
        el.className = 'now-singing-empty';
        if (state.queue.length > 0) {
            el.innerHTML = `
                <p>Ready to start</p>
                <button class="btn btn-success" onclick="nextSinger()" style="margin-top:12px">
                    Start First Singer
                </button>
            `;
        } else {
            el.innerHTML = '<p>No singers in queue yet</p>';
        }
    }
}

function renderQueue() {
    const list = document.getElementById('queue-list');
    if (!list) return;

    if (state.queue.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <div class="icon">&#127908;</div>
                <p>Queue is empty — add singers from the panel on the right</p>
            </div>
        `;
        return;
    }

    list.innerHTML = state.queue.map(item => `
        <div class="queue-item">
            <div class="position ${item.position <= 3 ? 'top-3' : ''}">${item.position}</div>
            <div class="info">
                <div class="name">
                    ${esc(item.name)}
                    ${item.tip_amount > 0 ? `<span class="tip-badge">$${item.tip_amount.toFixed(0)}</span>` : ''}
                </div>
                <div class="song">${esc(item.song_title)} — ${esc(item.song_artist)}</div>
                <div class="meta">
                    <span>Songs sung: ${item.songs_sung}</span>
                    ${item.tip_total > 0 ? `<span style="color:var(--tip-gold)">Tips: $${item.tip_total.toFixed(0)}</span>` : ''}
                </div>
            </div>
            <div class="actions">
                <button class="btn-tip" onclick="addQueueTip(${item.position})" title="Add tip">$</button>
                <button class="btn-icon" onclick="moveToTop(${item.position})" title="Move to top">&uarr;</button>
                <button class="btn-icon" onclick="removeSinger(${item.position})" title="Remove" style="color:var(--red)">&times;</button>
            </div>
        </div>
    `).join('');
}

function renderSearchResults(results) {
    const el = document.getElementById('search-results');
    if (!results || results.length === 0) {
        el.innerHTML = '<div style="padding:14px;color:var(--text-secondary)">No songs found</div>';
        return;
    }

    el.innerHTML = results.map((song, i) => `
        <div class="search-result" onclick='selectSong(${JSON.stringify(song).replace(/'/g, "\\'")})'>
            <span class="song-score">${song.score}%</span>
            <div class="song-title">${esc(song.title)}</div>
            <div class="song-artist">${esc(song.artist)}${song.disc_id ? ` (${esc(song.disc_id)})` : ''}</div>
        </div>
    `).join('');
}

function renderTipButtons() {
    const el = document.getElementById('tip-buttons');
    if (!el) return;

    const amounts = [0, 5, 10, 20];
    el.innerHTML = amounts.map(a =>
        `<button class="tip-btn ${state.selectedTip === a ? 'active' : ''}" onclick="selectTip(${a})">
            ${a === 0 ? 'None' : '$' + a}
        </button>`
    ).join('') +
    `<button class="tip-btn ${!amounts.includes(state.selectedTip) && state.selectedTip > 0 ? 'active' : ''}"
             onclick="customTip()">
        ${!amounts.includes(state.selectedTip) && state.selectedTip > 0 ? '$' + state.selectedTip : 'Custom'}
    </button>`;
}

function renderStats() {
    const el = document.getElementById('header-stats');
    if (!el) return;
    const s = state.stats;
    if (!state.sessionActive) {
        el.innerHTML = '';
        return;
    }
    el.innerHTML = `
        <span>Singers: <span class="stat-value">${s.total_singers || 0}</span></span>
        <span>Songs: <span class="stat-value">${s.total_songs || 0}</span></span>
        <span>In Queue: <span class="stat-value">${s.in_queue || 0}</span></span>
        <span>Tips: <span class="stat-value">$${(s.tips_total || 0).toFixed(0)}</span></span>
    `;
}

// ---- Settings ----
async function openSettings() {
    const config = await API.get('/api/config');
    document.getElementById('setting-folders').value = (config.song_folders || []).join('\n');
    document.getElementById('setting-tip-weight').value = config.tip_weight;
    document.getElementById('setting-venue').value = config.venue;
    document.getElementById('song-count-display').textContent = `${config.song_count} songs indexed`;
    document.getElementById('settings-modal').classList.add('active');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.remove('active');
}

async function saveSettings() {
    const folders = document.getElementById('setting-folders').value
        .split('\n').map(f => f.trim()).filter(f => f);
    const tipWeight = parseInt(document.getElementById('setting-tip-weight').value) || 50;
    const venue = document.getElementById('setting-venue').value.trim() || 'Chaplins';

    await API.post('/api/config', {
        song_folders: folders,
        tip_weight: tipWeight,
        venue: venue,
    });

    // Rescan songs with new folders
    const scanResult = await API.post('/api/songs/rescan');
    showToast(`Settings saved. ${scanResult.count} songs indexed in ${scanResult.scan_time}s`);
    closeSettings();
}

// ---- History Tab ----
async function showHistory() {
    const data = await API.get('/api/session/history');
    const el = document.getElementById('history-content');
    if (!data || data.length === 0) {
        el.innerHTML = '<div class="empty-state"><p>No singers yet tonight</p></div>';
        return;
    }
    el.innerHTML = `
        <table class="history-table">
            <thead><tr>
                <th>Singer</th><th>Songs</th><th>Tips</th><th>Song List</th>
            </tr></thead>
            <tbody>
                ${data.map(r => `<tr>
                    <td>${esc(r.name)}</td>
                    <td>${r.songs_sung}</td>
                    <td>${r.tip_total > 0 ? '$' + r.tip_total.toFixed(0) : '-'}</td>
                    <td style="color:var(--text-secondary);font-size:0.85rem">${esc(r.songs_list || '-')}</td>
                </tr>`).join('')}
            </tbody>
        </table>
    `;
}

// ---- Tab Switching ----
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).style.display = 'block';

    if (tabName === 'history') showHistory();
}

// ---- Utilities ----
function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

function showToast(msg) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function setupEventListeners() {
    setupSongSearch();

    // Enter key on singer name focuses song search
    const nameInput = document.getElementById('singer-name');
    if (nameInput) {
        nameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('song-search').focus();
            }
        });
    }

    // Keyboard shortcut: Ctrl+Enter to add singer
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            addSinger();
        }
    });
}
