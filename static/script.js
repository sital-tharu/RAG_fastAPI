document.addEventListener('DOMContentLoaded', () => {
    const ingestBtn = document.getElementById('ingestBtn');
    const tickerInput = document.getElementById('tickerInput');
    const ingestStatus = document.getElementById('ingestStatus');
    const sendBtn = document.getElementById('sendBtn');
    const queryInput = document.getElementById('queryInput');
    const chatContainer = document.getElementById('chatContainer');

    // Ingestion Logic
    ingestBtn.addEventListener('click', async () => {
        const ticker = tickerInput.value.trim().toUpperCase();
        if (!ticker) return;

        ingestBtn.disabled = true;
        ingestBtn.textContent = '...';
        ingestStatus.className = 'status-msg';
        ingestStatus.textContent = 'Ingesting data...';

        try {
            const response = await fetch('/api/v1/ingest/company', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker })
            });

            if (response.ok) {
                const data = await response.json();
                ingestStatus.className = 'status-msg status-success';
                ingestStatus.textContent = `Success! Added ${data.statements} statements.`;
                // Optionally save ticker to context
                localStorage.setItem('currentTicker', ticker);
            } else {
                const error = await response.json();
                ingestStatus.className = 'status-msg status-error';
                ingestStatus.textContent = error.detail || 'Ingestion failed';
            }
        } catch (e) {
            ingestStatus.className = 'status-msg status-error';
            ingestStatus.textContent = 'Network Error';
        } finally {
            ingestBtn.disabled = false;
            ingestBtn.textContent = 'Ingest';
        }
    });

    // Chat Logic
    const appendMessage = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (sender === 'bot') {
            contentDiv.innerHTML = marked.parse(text);
        } else {
            contentDiv.textContent = text;
        }

        msgDiv.appendChild(contentDiv);
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return contentDiv;
    };

    const handleQuery = async () => {
        const query = queryInput.value.trim();
        const ticker = localStorage.getItem('currentTicker') || tickerInput.value.trim().toUpperCase();

        if (!query) return;
        if (!ticker) {
            alert('Please ingest a company ticker first (or enter one in the sidebar).');
            return;
        }

        appendMessage(query, 'user');
        queryInput.value = '';

        // Loading State
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.innerHTML = '<div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
        chatContainer.appendChild(loadingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        try {
            const response = await fetch('/api/v1/query/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker, query: query })
            });

            if (response.ok) {
                const data = await response.json();
                chatContainer.removeChild(loadingDiv);
                appendMessage(data.answer, 'bot');
            } else {
                const error = await response.json();
                chatContainer.removeChild(loadingDiv);
                appendMessage(`Error: ${error.detail || 'Failed to get answer'}`, 'bot');
            }
        } catch (e) {
            chatContainer.removeChild(loadingDiv);
            appendMessage('Network Error: Could not reach server.', 'bot');
        }
    };

    sendBtn.addEventListener('click', handleQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleQuery();
        }
    });
});
