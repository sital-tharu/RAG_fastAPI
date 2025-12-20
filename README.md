# Financial RAG Agent

A premium, strictly governed Retrieval-Augmented Generation (RAG) system designed for accurate financial analysis of Indian stocks (NSE).

![Financial RAG UI](static/screenshot_placeholder.png)

## Features

### 1. 🛡️ Strict Financial Governance
- **Zero Hallucination Policy**: Refuses to answer queries outside the provided data.
- **Stock Prediction Firewall**: Explicitly refuses to forecast stock prices.
- **Capital Expenditure Logic**: Correctly misinterprets negative Cash Flow values as outflows, with clear explanations.
- **Citation System**: Every fact is cited with `[Source: FYxxxx (Statement Type)]`.

### 2. 📊 Comprehensive Data Analysis
- **Historical Data**: Access to full Annual and Quarterly data (e.g., FY2021-FY2025).
- **Core Statements**:
  - Income Statement (Revenue, Net Profit, Margins)
  - Balance Sheet (Assets, Liabilities, Equity)
  - Cash Flow (CapEx, Operating Cash)
- **Ratio Calculation**: Automatically calculates key metrics if not present.

### 3. 💎 Premium Experience
- **Dark Mode UI**: Glassmorphism design with responsive chat interface.
- **Windows Optimized**: Custom backend architecture to prevent `asyncio` crashes on Windows.
- **Smart Formatting**: Markdown rendering for clear, readable financial summaries.

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/sital-tharu/RAG_fastAPI.git
   cd RAG_fastAPI
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Requires Python 3.10+*

3. **Configure Environment**
   Create a `.env` file:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
   ```

## Usage

### 1. Start the Server
```bash
python run.py
```
Access the app at `http://localhost:8000`.

### 2. Ingest Data (Windows-Safe)
Use the included script for reliable ingestion:
```bash
# Default (TCS.NS)
python ingest_data.py

# specific Ticker
python ingest_data.py RELIANCE.NS
```
*Note: You can also use the "Ingest" button in the Web UI.*

### 3. Ask Questions
- **Historical**: "What was the Total Revenue in FY 2022?"
- **Analysis**: "What is the Net Profit Margin for the latest year?"
- **Governance Test**: "Will the stock price go up?" (Should be refused)

## Technology Stack
- **Backend**: FastAPI, SQLAlchemy (Async), PostgreSQL
- **AI/LLM**: Google Gemini 2.5 Flash, LangChain
- **Frontend**: HTML5, Vanilla JS, Glassmorphism CSS
- **Vector Store**: ChromaDB (Conditional/Platform-Aware)
