# Financial RAG Agent

A premium, governed AI assistant for analyzing Indian stock market data.

## Features
- **Strict Governance**: Zero hallucinations, citation required.
- **Data Support**: Annual & Quarterly Income, Balance Sheet, and Cash Flows.
- **Premium UI**: Dark mode with glassmorphism design.

## Quick Start

### 1. Requirements
- Python 3.10+
- PostgreSQL
- Google Gemini API Key

### 2. Setup
```bash
git clone https://github.com/sital-tharu/RAG_fastAPI.git
cd RAG_fastAPI
pip install -r requirements.txt
```

Create a `.env` file:
```env
GOOGLE_API_KEY=your_key
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
```

### 3. Run
```bash
python run.py
```
Open [http://localhost:8000](http://localhost:8000).

### 4. How to Use
1. **Ingest**: Type a ticker (e.g., `RELIANCE.NS`) in the Web UI or run `python ingest_data.py RELIANCE.NS`.
2. **Ask**: Query for Revenue, Margins, or CapEx.

---
*Powered by FastAPI, LangChain, and Google Gemini.*
