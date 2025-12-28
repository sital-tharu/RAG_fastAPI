# Financial RAG System

A production-grade AI assistant for analyzing financial statements of publicly traded Indian companies (NSE/BSE).

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## What It Does

Ask natural language questions about a company's financials, and get accurate, citation-backed answers:

| Question | Answer |
|----------|--------|
| "What is the revenue for INFY.NS?" | "The Operating Revenue is ₹5,076,000,000 [Source: FY2025 Q3, Income Statement]" |
| "What is the net profit?" | "Net Income is ₹200,000,000 [Source: FY2025 Q3, Income Statement]" |
| "Will the stock go up?" | "Cannot determine from available data." (Speculation refused) |

## Key Features

- **Hybrid Retrieval**: SQL for exact numbers + Vector search for semantic matching
- **Anti-Hallucination**: Strict prompts ensure LLM only uses provided data
- **Multi-Statement**: Income Statement, Balance Sheet, Cash Flow (Annual & Quarterly)
- **Rate-Limit Resilient**: Graceful retries with exponential backoff

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (running locally or remote)
- Groq API Key ([Get one free](https://console.groq.com))

### 1. Clone & Install
```bash
git clone https://github.com/sital-tharu/RAG_fastAPI.git
cd RAG_fastAPI
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file:
```env
groq_api_key=your_groq_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/financial_rag
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Run the Server
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 5. Usage
1. **Ingest a Company**: Enter a ticker (e.g., `INFY.NS`, `TCS.NS`, `RELIANCE.NS`) and click the download button.
2. **Ask Questions**: Type questions like "What is the revenue?" or "Show me total assets."

## Project Structure

```
RAG_fastAPI/
├── app/
│   ├── api/routes/          # FastAPI endpoints
│   ├── core/                # Database, config, vector store
│   ├── ingestion/           # Data fetching & normalization
│   ├── llm/                 # Groq integration & prompts
│   ├── models/              # SQLAlchemy models
│   └── retrieval/           # SQL & Vector retrievers
├── static/                  # Web UI (HTML/CSS/JS)
├── documentation.md         # Full technical documentation
├── run.py                   # Entry point
└── requirements.txt         # Dependencies
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Uvicorn |
| Database | PostgreSQL + SQLAlchemy (async) |
| Vector Store | ChromaDB |
| LLM | Groq (`llama-3.1-8b-instant`) |
| Data Source | Yahoo Finance (`yfinance`) |

## Documentation

For a comprehensive technical deep-dive (architecture diagrams, RAG pipeline, rate-limit handling, evaluation), see:

📖 **[documentation.md](documentation.md)**

## Limitations

- **Numeric Only**: Currently answers questions about numbers (Revenue, Profit, Assets). Qualitative queries ("What are the risks?") are not supported.
- **Rate Limits**: Free Groq tier allows ~14k requests/day. Heavy usage may hit limits.
- **Coverage**: Data availability depends on Yahoo Finance.

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built with ❤️ using FastAPI, LangChain, and Groq.*
