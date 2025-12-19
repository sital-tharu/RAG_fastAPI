# Financial RAG FastAPI Application

A powerful Retrieval-Augmented Generation (RAG) system built with FastAPI, designed to answer financial questions by ingesting and analyzing data from Yahoo Finance. This project combines the power of SQL (PostgreSQL) for structured data and Vector Search (ChromaDB) for semantic understanding, powered by Google's Gemini LLM.

## 🚀 Features

-   **Automated Ingestion**: Fetches and normalizes financial statements (Income Statement, Balance Sheet, Cash Flow) using `yfinance`.
-   **Hybrid RAG Pipeline**: Combines structured SQL queries with vector similarity search for high-precision retrieval.
-   **Google Gemini Integration**: Utilizes Google's Gemini-Pro model for generating insightful, context-aware answers.
-   **Modern Web Interface**: A sleek, dark-themed UI for chatting with the AI and managing verified company data.
-   **FastAPI Backend**: High-performance, asynchronous REST API with auto-generated documentation.
-   **Vector Search**: Uses `all-MiniLM-L6-v2` embeddings via ChromaDB for semantic context retrieval.

## 🛠️ Tech Stack

-   **Backend**: Python 3.10+, FastAPI, Uvicorn
-   **Database**: PostgreSQL (SQLAlchemy + AsyncPG)
-   **Vector Store**: ChromaDB
-   **AI/LLM**: Google Gemini (via `langchain-google-genai`), Sentence Transformers
-   **Frontend**: Vanilla HTML5, CSS3, JavaScript
-   **Data Source**: Yahoo Finance

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

-   **Python 3.10** or higher
-   **PostgreSQL** (running locally or accessible via URL)
-   **Git**

You will also need a **Google API Key** for Gemini.

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/sital-tharu/RAG_fastAPI.git
    cd RAG_fastAPI
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    
    # Windows
    .\venv\Scripts\Activate.ps1
    
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory and add your credentials:
    ```env
    # Database Configuration
    DATABASE_URL=postgresql+asyncpg://user:password@localhost/financial_rag
    
    # Google Gemini API Key
    GOOGLE_API_KEY=your_google_api_key_here
    
    # Optional Settings
    DEBUG=True
    LOG_LEVEL=INFO
    ```

5.  **Initialize the Database**
    Run the initialization script to create tables and schema:
    ```bash
    python init_db.py
    ```

## 🏃‍♂️ Running the Application

This project includes a custom runner `run.py` to handle Windows-specific asyncio setups gracefully.

**Start the Server:**
```bash
python run.py
```

-   **Web UI**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
-   **API Documentation**: Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the Swagger UI.

## 📖 Usage Guide

### 1. Ingest Data
Use the Web UI or the API to ingest financial data for a company.
-   **UI**: Enter a ticker symbol (e.g., `RELIANCE.NS`, `TCS.NS`, `INFY.NS`) in the "Ingest Ticker" box and click "Ingest".
-   **API**: `POST /api/v1/ingest/company/{ticker}`

### 2. Chat with Data
Once data is ingested, you can ask questions like:
-   "What was the total revenue of RELIANCE in 2023?"
-   "Compare the net income of TCS over the last 3 years."
-   "What are the major expenses for INFY?"

The system will retrieve relevant financial context and generate an answer using Gemini.

## 📂 Project Structure

```
RAG_fastAPI/
├── app/
│   ├── api/            # API Routes (Endpoints)
│   ├── core/           # Config, Vector Store setup
│   ├── ingestion/      # Data fetching & normalization logic
│   ├── llm/            # LLM service & prompt templates
│   ├── retrieval/      # Hybrid retrieval logic (SQL + Vector)
│   └── main.py         # FastAPI App factory
├── static/             # Frontend assets (HTML/CSS/JS)
├── database/           # Database migrations/models
├── run.py              # Application entry point
├── init_db.py          # Database initialization script
└── requirements.txt    # Project dependencies
```

## 🧪 Running Tests

To run the test suite:
```bash
pytest
```
