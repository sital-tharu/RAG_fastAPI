const API_BASE = "/api/v1";

// DOM Elements
const messagesContainer = document.getElementById('messages');
const queryInput = document.getElementById('queryInput');
const tickerInput = document.getElementById('tickerInput');
const ingestStatus = document.getElementById('ingestStatus');
const ingestBtn = document.getElementById('ingestBtn');

// Auto-resize textarea
queryInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
}

function appendMessage(role, text, isLoading = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerText = role === 'user' ? 'You' : 'AI';

    // Bubble
    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (isLoading) {
        bubble.innerHTML = '<div class="typing-indicator">Analyzing...</div>';
        msgDiv.id = 'loading-msg';
    } else {
        // Parse Markdown if AI
        if (role === 'ai') {
            bubble.innerHTML = marked.parse(text);
        } else {
            bubble.innerText = text;
        }
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    messagesContainer.appendChild(msgDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function ingestCompany() {
    const ticker = tickerInput.value.trim().toUpperCase();
    if (!ticker) return;

    ingestBtn.disabled = true;
    ingestStatus.innerHTML = '<span style="color: var(--text-secondary)">Ingesting... <span class="spin">⟳</span></span>';

    try {
        const res = await fetch(`${API_BASE}/ingest/company`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker })
        });

        const data = await res.json();

        if (res.ok) {
            ingestStatus.innerHTML = `<span class="status-pill status-success">Ingested ${ticker}</span>`;
            // Optional: Store current ticker globally
            window.currentTicker = ticker;
        } else {
            ingestStatus.innerHTML = `<span class="status-pill status-error">Error: ${data.detail || 'Failed'}</span>`;
        }
    } catch (e) {
        ingestStatus.innerHTML = `<span class="status-pill status-error">Network Error</span>`;
    } finally {
        ingestBtn.disabled = false;
    }
}

async function sendQuery() {
    const text = queryInput.value.trim();
    const ticker = tickerInput.value.trim().toUpperCase() || window.currentTicker || "INFY.NS"; // Default fallback

    if (!text) return;

    // UI Updates
    queryInput.value = '';
    queryInput.style.height = 'auto';
    appendMessage('user', text);
    appendMessage('ai', '', true); // Loading state

    try {
        const res = await fetch(`${API_BASE}/query/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, ticker: ticker })
        });

        const data = await res.json();
        const loadingMsg = document.getElementById('loading-msg');
        if (loadingMsg) loadingMsg.remove();

        if (res.ok) {
            // Display Answer
            // We can also display classification info if desired (data.query_type)
            appendMessage('ai', data.answer);
        } else {
            appendMessage('ai', `**Error**: ${data.detail || 'Something went wrong.'}`);
        }
    } catch (e) {
        const loadingMsg = document.getElementById('loading-msg');
        if (loadingMsg) loadingMsg.remove();
        appendMessage('ai', `**Network Error**: Could not reach server. System might be down.`);
    }
}
