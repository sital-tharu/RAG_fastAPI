document.addEventListener('DOMContentLoaded', () => {
    const ingestBtn = document.getElementById('ingestBtn');
    const tickerInput = document.getElementById('tickerInput');
    const ingestStatus = document.getElementById('ingestStatus');
    const sendBtn = document.getElementById('sendBtn');
    const queryInput = document.getElementById('queryInput');
    const chatContainer = document.getElementById('chatContainer');

    // Auto-resize textarea
    queryInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value === '') this.style.height = '50px';
    });

    // Ingestion Logic
    ingestBtn.addEventListener('click', async () => {
        const ticker = tickerInput.value.trim().toUpperCase();
        if (!ticker) return;

        ingestBtn.disabled = true;
        ingestBtn.innerHTML = '<span class="btn-text">Ingesting...</span>';
        ingestStatus.className = 'status-indicator';
        ingestStatus.textContent = 'Processing financial data...';

        try {
            const response = await fetch('/api/v1/ingest/company', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker })
            });

            if (response.ok) {
                const data = await response.json();
                ingestStatus.className = 'status-indicator status-success';
                ingestStatus.textContent = `Success!`;
                localStorage.setItem('currentTicker', ticker);
                appendMessage(`Successfully ingested data for ${ticker}. You can now ask questions!`, 'bot');
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Ingestion failed');
            }
        } catch (e) {
            ingestStatus.className = 'status-indicator status-error';
            ingestStatus.textContent = 'Error (Check Console)';
            console.error(e);
            appendMessage(`<strong>Ingestion Error:</strong> The server might be unstable on Windows. <br>Please run <code>python ingest_data.py ${ticker}</code> in your terminal instead.`, 'bot');
        } finally {
            ingestBtn.disabled = false;
            ingestBtn.innerHTML = '<span class="btn-text">Ingest Data</span><div class="btn-shine"></div>';
        }
    });

    // Chat Logic
    const appendMessage = (text, sender) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender === 'user' ? 'user-message' : 'bot-message'}`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar';
        avatarDiv.textContent = sender === 'user' ? 'ME' : 'AI';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (sender === 'bot') {
            contentDiv.innerHTML = marked.parse(text);
        } else {
            contentDiv.textContent = text;
        }

        if (sender === 'user') {
            msgDiv.appendChild(contentDiv);
            msgDiv.appendChild(avatarDiv);
        } else {
            msgDiv.appendChild(avatarDiv);
            msgDiv.appendChild(contentDiv);
        }

        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return msgDiv; // Return div to remove later if needed (loading)
    };

    const handleQuery = async () => {
        const query = queryInput.value.trim();
        const ticker = localStorage.getItem('currentTicker') || tickerInput.value.trim().toUpperCase();

        if (!query) return;
        if (!ticker) {
            alert('Please ingest a company ticker first.');
            return;
        }

        appendMessage(query, 'user');
        queryInput.value = '';
        queryInput.style.height = '50px';

        // Loading Indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.innerHTML = `
            <div class="avatar">AI</div>
            <div class="message-content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>`;
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
                throw new Error(error.detail || 'Data retrieval failed');
            }
        } catch (e) {
            chatContainer.removeChild(loadingDiv);
            console.error(e);
            appendMessage(`<strong>Network Error:</strong> Could not connect to the backend. <br>Please check if <code>python run.py</code> is running.`, 'bot');
        }
    };

    sendBtn.addEventListener('click', handleQuery);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleQuery();
        }
    });

    // Suggestion Chips Logic
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.textContent.substring(2).trim(); // Remove emoji

            // Special handling for Historical
            if (query.includes('Revenue FY2022')) {
                queryInput.value = "What was the total revenue in FY 2022?";
            } else {
                queryInput.value = "What is the " + query + "?";
            }

            handleQuery();
        });
    });
});
