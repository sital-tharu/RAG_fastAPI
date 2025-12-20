# Financial RAG System - Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Ingestion Pipeline](#ingestion-pipeline)
4. [Data Processing](#data-processing)
5. [Retrieval Logic](#retrieval-logic)
6. [Challenges Solved](#challenges-solved)
7. [Verification & Testing](#verification--testing)
8. [Deployment Considerations](#deployment-considerations)

---

## System Overview

The Financial RAG (Retrieval-Augmented Generation) system is a production-grade AI assistant designed to analyze financial statements of Indian public companies (NSE/BSE). It combines structured SQL retrieval with semantic vector search to provide accurate, citation-backed financial insights.

**Core Technologies:**
- **Backend Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (structured financial data storage)
- **Vector Store**: ChromaDB (semantic embeddings)
- **LLM**: Google Gemini 2.5 Flash (via LangChain)
- **Data Source**: Yahoo Finance API (`yfinance`)

**Key Features:**
- Historical data access (FY2021-FY2025, Annual & Quarterly)
- Strict governance (zero hallucinations, mandatory citations)
- Multi-statement support (Income, Balance Sheet, Cash Flow)
- Metadata-based filtering (ticker, fiscal year, period type)

---

## Architecture

### High-Level Flow
```
User Query → FastAPI → HybridRetriever → [SQL + Vector Search] → Context Builder → Gemini LLM → Response
```

### Component Diagram
```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (HTML/CSS/JS)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI Application (main.py)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │  API Routes (/ingest, /query, /health)          │   │
│  └──────────────────┬───────────────────────────────┘   │
└───────────────────┬─┴─────────────────────────────────┬─┘
                    │                                   │
        ┌───────────▼─────────────┐     ┌──────────────▼────────────┐
        │  Ingestion Service      │     │  HybridRetriever          │
        │  ┌──────────────────┐   │     │  ┌─────────────────────┐  │
        │  │ YahooFinance     │   │     │  │ QueryClassifier     │  │
        │  │ Fetcher          │   │     │  │ (Numeric/Factual)   │  │
        │  └──────┬───────────┘   │     │  └──────┬──────────────┘  │
        │  ┌──────▼───────────┐   │     │  ┌──────▼──────────────┐  │
        │  │ DataNormalizer   │   │     │  │ SQLRetriever        │  │
        │  │ (Chunking)       │   │     │  │ (Metadata Filter)   │  │
        │  └──────┬───────────┘   │     │  └──────┬──────────────┘  │
        └─────────┼───────────────┘     │  ┌──────▼──────────────┐  │
                  │                     │  │ VectorStore         │  │
        ┌─────────▼───────────────┐     │  │ (ChromaDB)          │  │
        │  PostgreSQL Database    │     │  └─────────────────────┘  │
        │  ┌──────────────────┐   │     └───────────┬────────────────┘
        │  │ Companies        │   │                 │
        │  │ Statements       │◄──┼─────────────────┘
        │  │ LineItems        │   │
        │  └──────────────────┘   │     ┌──────────────────────────┐
        └──────────────────────────┘     │  LLM Service (Gemini)    │
                                        │  ┌────────────────────┐  │
                                        │  │ Prompt Template    │  │
                                        │  │ (Strict Rules)     │  │
                                        │  └────────────────────┘  │
                                        └──────────────────────────┘
```

---

## Ingestion Pipeline

### 1. Data Fetching (`app/ingestion/data_fetchers.py`)

**YahooFinanceFetcher** pulls financial data from Yahoo Finance using NSE/BSE tickers:

```python
async def fetch_financials(self, ticker: str) -> Dict[str, Any]:
    # Runs yfinance in a separate thread to avoid blocking async loop
    return await asyncio.to_thread(self._fetch_sync, ticker)
```

**Data Retrieved:**
- **Balance Sheets** (Annual + Quarterly): `stock.balance_sheet`, `stock.quarterly_balance_sheet`
- **Income Statements** (Annual + Quarterly): `stock.income_stmt`, `stock.quarterly_income_stmt`
- **Cash Flow Statements** (Annual + Quarterly): `stock.cashflow`, `stock.quarterly_cashflow`
- **Company Metadata**: `stock.info` (name, sector, industry)

**Output Format:**
```python
{
    "info": {...},
    "balance_sheet": {"annual": {...}, "quarterly": {...}},
    "income_statement": {"annual": {...}, "quarterly": {...}},
    "cash_flow": {"annual": {...}, "quarterly": {...}}
}
```

### 2. Data Normalization (`app/ingestion/data_normalizer.py`)

**DataNormalizer** converts raw pandas DataFrames into structured `StandardizedFinancials` objects:

**Normalization Steps:**
1. **Parse Dates**: Extract `period_date` from DataFrame column headers
2. **Extract Line Items**: Convert index (row labels) into `LineItem(name, value)` pairs
3. **Calculate Fiscal Metadata**: Derive `fiscal_year` and `fiscal_quarter`
4. **Filter Invalid Data**: Skip `None` values and non-numeric entries

**Output Schema:**
```python
class StandardizedFinancials:
    statement_type: str        # "balance_sheet" | "income_statement" | "cash_flow"
    period_type: str           # "annual" | "quarterly"
    period_date: datetime
    fiscal_year: int
    fiscal_quarter: Optional[int]
    line_items: List[LineItem]
    raw_data: Dict
```

### 3. Database Persistence (`app/ingestion/ingestion_service.py`)

**IngestionService** orchestrates the full pipeline:

1. **Fetch** → `YahooFinanceFetcher.fetch_financials(ticker)`
2. **Normalize** → `DataNormalizer.normalize(raw_data)`
3. **Store in PostgreSQL**:
   - **Companies Table**: Upsert company metadata (ticker, name, sector)
   - **FinancialStatements Table**: Insert statements with unique constraint:
     ```sql
     CONSTRAINT uq_company_statement_period UNIQUE (company_id, statement_type, period_type, period_date)
     ```
   - **FinancialLineItems Table**: Insert line items with unique constraint:
     ```sql
     CONSTRAINT uq_statement_line_item UNIQUE (statement_id, line_item_name)
     ```
4. **Prepare Vector Chunks**: For each line item, create a formatted text chunk:
   ```
   Company: Reliance Industries (RELIANCE.NS)
   Period: 2023-03-31 (annual)
   Statement: income_statement
   Line Item: Total Revenue
   Value: 6,959,630,000,000.00
   ```
5. **Store in ChromaDB**: `vector_store.add_texts(chunks, metadatas)`

**Metadata Schema:**
```python
{
    "company_id": int,
    "ticker": str,
    "statement_type": str,
    "period_type": str,
    "period_date": str (ISO format),
    "line_item": str,
    "numeric_value": float
}
```

---

## Data Processing

### Chunking Strategy

**Challenge**: Financial statements are tabular (columns = dates, rows = line items). Traditional text chunking would destroy this structure.

**Solution**: **Per-Line-Item Chunking**
- Each financial line item (e.g., "Total Revenue") becomes a single chunk
- Preserves context (company, date, statement type) within each chunk
- Enables precise retrieval: "Revenue for FY2022" matches the exact chunk

**Advantages:**
1. **Granular Retrieval**: Query "What is CapEx?" retrieves only CapEx-related chunks
2. **Metadata Filtering**: Filter by ticker (prevent data mix-ups across companies)
3. **Temporal Accuracy**: Filter by fiscal year (e.g., FY2022 vs FY2023)

**Example Chunk:**
```
Company: TCS (TCS.NS)
Period: 2022-03-31 (annual)
Statement: cash_flow
Line Item: Capital Expenditure
Value: -139,000,000,000.00
```

### Embedding Model

**Model**: `sentence-transformers/all-MiniLM-L6-v2` (via ChromaDB)
- Compact (384-dimensional embeddings)
- Fast inference
- Trained on semantic similarity tasks

---

## Retrieval Logic

### Hybrid Retrieval Architecture (`app/retrieval/hybrid_retriever.py`)

**Query Classification** → Determines which retriever(s) to use:
- **NUMERIC**: "What is the revenue?" → SQL only
- **FACTUAL**: "Explain the company's business model" → Vector only
- **HYBRID**: "Compare revenue to debt" → SQL + Vector

### 1. SQL Retrieval (`app/retrieval/sql_retriever.py`)

**Purpose**: Retrieve structured numerical data with high confidence.

**Query Parsing:**
1. **Keyword Extraction**: Split query into words (length > 3)
2. **Year Extraction**: Regex to find fiscal years:
   ```python
   year_match = re.search(r'(?:20|FY)(\d{2})', query_text)
   # "FY22" → 2022, "FY 2023" → 2023
   ```
3. **Fuzzy Matching**: Use `ILIKE` to match line item names:
   ```sql
   WHERE (line_item_name ILIKE '%revenue%' OR line_item_name ILIKE '%profit%')
   AND fiscal_year = 2022
   ```

**SQL Query:**
```sql
SELECT 
    line_item_name,
    line_item_value,
    fiscal_year,
    statement_type,
    period_type
FROM financial_line_items
JOIN financial_statements ON ...
WHERE company_id = ? AND (keyword_matches) AND fiscal_year = ?
ORDER BY period_date DESC
LIMIT 100
```

**Output:**
```python
{
    "source": "sql",
    "line_item": "Total Revenue",
    "value": 6959630000000.0,
    "period": "FY2022 (Annual)",
    "statement": "income_statement"
}
```

### 2. Vector Retrieval (`app/core/vector_store.py`)

**Purpose**: Semantic search for qualitative/contextual queries.

**Similarity Search:**
```python
results = collection.query(
    query_texts=["What is the operating margin?"],
    n_results=5,
    where={"ticker": "RELIANCE.NS"}  # Metadata filter
)
```

**Metadata Filtering** (Critical for preventing data mix-ups):
- **Ticker Filter**: Ensures only the queried company's data is retrieved
- **Period Filter** (optional): e.g., `period_date >= "2023-01-01"`

**Distance Metric**: Cosine similarity (default in ChromaDB)

### 3. Context Building

**HybridRetriever** merges SQL and Vector results into a single context string:

```
=== STRUCTURED FINANCIAL DATA (High Confidence) ===
- Total Revenue: 6,959,630,000,000 (FY2022 (Annual), income_statement)
- Net Income: 602,150,000,000 (FY2022 (Annual), income_statement)

=== TEXTUAL CONTEXT FRAGMENTS ===
- Company: Reliance Industries (RELIANCE.NS) | Period: 2022-03-31 | ...
```

This context is sent to the LLM with the strict governance prompt.

---

## Challenges Solved

### 1. Windows AsyncIO Loop Crash

**Problem**: ChromaDB uses SQLite, which is not thread-safe. On Windows, the ProactorEventLoop caused:
```
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread
```

**Solution**: `asyncio.run_in_executor()` with thread-local ChromaDB clients

**Implementation** (`app/core/vector_store.py`):
```python
def _get_collection_sync(self):
    # Create client in CURRENT THREAD context
    client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
    return client.get_or_create_collection(...)

async def add_texts(self, texts, metadatas):
    def _add_sync():
        collection = self._get_collection_sync()  # Client created in this thread
        collection.add(documents=texts, metadatas=metadatas, ids=ids)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _add_sync)  # Runs in ThreadPoolExecutor
```

**Fallback**: On Windows, vector operations are skipped entirely if stability issues persist:
```python
if sys.platform == "win32":
    return  # Skip vector ingestion on Windows
```

### 2. Hallucination Prevention (Strict Source-Grounding)

**Problem**: LLMs may fabricate data or calculate incorrect ratios.

**Solution**: Multi-layered governance system

**Layer 1: System Prompt** (`app/llm/prompt_templates.py`):
```python
FINANCIAL_QA_PROMPT_STR = """
1. DATA SCOPE & SOURCE OF TRUTH
- You may ONLY use the data explicitly provided to you in the CONTEXT.
- You MUST NOT use any external knowledge, prior training data, or assumptions.

2. NUMERIC GOVERNANCE (CRITICAL)
- ALL numeric values are computed OUTSIDE the LLM.
- You MUST NOT perform any arithmetic calculations yourself.

3. CAPITAL EXPENDITURE (CAPEX) RULE
- Negative CapEx values represent a cash outflow for investing activities.
- You MUST explicitly state that CapEx is sourced from the Cash Flow Statement.

4. CITATION REQUIREMENT
- Every factual statement must include a citation indicating:
  - Fiscal year
  - Statement type
- Example: [Source: FY2022 (Annual), Income Statement]

5. REFUSAL & SAFETY RULES
- You MUST refuse to answer stock price predictions, future performance forecasts, etc.
- Use the exact refusal phrase: "Cannot determine from available data."
"""
```

**Layer 2: Temperature Control**:
```python
self.llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0  # Maximum factuality, zero creativity
)
```

**Layer 3: Context Validation**:
```python
if not context.strip():
    return "I cannot answer this question as no relevant financial data was found."
```

### 3. Historical Data Retrieval

**Problem**: Initially, queries like "Revenue in FY2022" failed because:
1. Default `LIMIT 20` was too small to reach older years
2. Annual data was mislabeled as "Q1" (generic first quarter)

**Solution**:
1. **Increased Retrieval Limit**: `limit=100` in SQL queries
2. **Year-based Filtering**: Regex to extract year from query
3. **Explicit Period Labeling**:
   ```python
   period = f"FY{fiscal_year} (Annual)" if period_type == "annual" 
           else f"FY{fiscal_year} Q{fiscal_quarter}"
   ```

---

## Verification & Testing

### Test Companies
- **Reliance Industries** (`RELIANCE.NS`): Conglomerate (Energy, Telecom, Retail)
- **TCS** (`TCS.NS`): IT Services
- **Infosys** (`INFY.NS`): IT Services

### Test Queries

**1. Numerical Queries (SQL Retrieval)**
```
Query: "What is the total revenue for FY 2022?"
Expected: Exact revenue value with citation [Source: FY2022 (Annual), Income Statement]
```

**2. Historical Queries (Year Filtering)**
```
Query: "What was the capital expenditure in FY 2021?"
Expected: Negative CapEx value explained as "cash outflow" + Cash Flow Statement citation
```

**3. Refusal Tests (Governance)**
```
Query: "Will Reliance stock go up next month?"
Expected: "Cannot determine from available data."
```

**4. Cash Flow Interpretation**
```
Query: "What is the CapEx?"
Expected: 
- Negative value shown
- Explicit mention: "This is a cash outflow"
- Citation: [Source: FY2025 (Annual), Cash Flow Statement]
```

### Verification Script (`ingest_data.py`)
```bash
# Ingest data for a company
python ingest_data.py RELIANCE.NS

# Query via Web UI
http://localhost:8000
```

### Database Verification
```sql
-- Check ingested companies
SELECT ticker, name, COUNT(statements.id) as statement_count
FROM companies
JOIN financial_statements ON companies.id = financial_statements.company_id
GROUP BY ticker, name;

-- Check fiscal year coverage
SELECT ticker, fiscal_year, COUNT(*) 
FROM financial_statements
JOIN companies ON companies.id = financial_statements.company_id
WHERE ticker = 'RELIANCE.NS'
GROUP BY ticker, fiscal_year
ORDER BY fiscal_year DESC;
```

---

## Deployment Considerations

### Environment Variables (`.env`)
```bash
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost/financial_rag
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEBUG=False
```

### Database Initialization
```bash
python init_db.py
```

### Running the Application
```bash
# Development
python run.py

# Production (with Gunicorn)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Windows-Specific Notes
1. **Vector Store**: Disabled by default on Windows to prevent crashes
2. **Event Loop Policy**: `WindowsSelectorEventLoopPolicy` is set automatically
3. **Ingestion**: Use `python ingest_data.py <ticker>` instead of Web UI ingestion

### Rate Limits
- **Yahoo Finance**: No official API limits, but avoid excessive requests
- **Gemini API**: 
  - Free tier: 60 queries/minute
  - Adjust `temperature=0.0` to minimize token usage

### Scaling Recommendations
1. **Database**: Use connection pooling (`max_overflow=10` in SQLAlchemy)
2. **Vector Store**: Consider Pinecone/Weaviate for production (better async support)
3. **Caching**: Add Redis for frequently queried companies
4. **Monitoring**: Integrate with Prometheus/Grafana for query latency tracking

---

## Appendix: Key Files Reference

| Component | File Path | Purpose |
|-----------|-----------|---------|
| Data Fetching | `app/ingestion/data_fetchers.py` | Yahoo Finance integration |
| Normalization | `app/ingestion/data_normalizer.py` | Raw data → StandardizedFinancials |
| Ingestion Service | `app/ingestion/ingestion_service.py` | Pipeline orchestration |
| SQL Retrieval | `app/retrieval/sql_retriever.py` | Structured data queries |
| Vector Store | `app/core/vector_store.py` | ChromaDB wrapper |
| Hybrid Retriever | `app/retrieval/hybrid_retriever.py` | SQL + Vector merging |
| LLM Service | `app/llm/llm_service.py` | Gemini integration |
| Governance Prompt | `app/llm/prompt_templates.py` | Anti-hallucination rules |
| Database Models | `app/models/models.py` | SQLAlchemy schemas |
| API Routes | `app/api/routes/` | FastAPI endpoints |

---


