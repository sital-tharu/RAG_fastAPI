# Financial RAG FastAPI Application

A Retrieval-Augmented Generation (RAG) system built with FastAPI, Google Gemini, and PostgreSQL to answer financial questions using 10-K/10-Q data.

## Features

- **Ingest**: Automated scraping and normalization of financial statements using `yfinance`.
- **RAG Pipeline**: Vector embeddings + SQL Retrieval for accurate context.
- **LLM Integration**: Uses Google Gemini Pro for generating answers.
- **LCEL Architecture**: Modern LangChain implementation using LangChain Expression Language.

## Prerequisites

- Python 3.9+
- PostgreSQL
- Google API Key

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sital-tharu/RAG_fastAPI.git
   cd RAG_fastAPI
   ```

2. **Install Dependencies**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/financial_rag
   GOOGLE_API_KEY=your_gemini_key
   ```

4. **Initialize Database**
   ```bash
   python init_db.py
   ```

## Running the Application

This project uses a custom runner to handle Windows Event Loop policies correctly.

```bash
python run.py
```

- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

## Project Structure

- `app/api`: API Routes
- `app/ingestion`: Data fetching and processing
- `app/llm`: Gemini & LangChain integration (using LCEL)
- `app/core`: Configuration & Vector Store
- `run.py`: Application entry point (Windows compatible)
