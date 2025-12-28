# Financial RAG System — Technical Documentation

> **Audience**: Final-year CS/IT students and engineers familiar with basic Python, APIs, and databases.  
> **Last Updated**: December 2024

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Technologies and Models](#3-technologies-and-models)
4. [RAG Pipeline](#4-rag-pipeline)
5. [Reliability and Rate-Limiting Handling](#5-reliability-and-rate-limiting-handling)
6. [Financial Data Use Case (INFY.NS Example)](#6-financial-data-use-case-infyns-example)
7. [Evaluation and Limitations](#7-evaluation-and-limitations)
8. [Conclusion](#8-conclusion)

---

## 1. Introduction

### 1.1 Problem Statement

Analyzing publicly traded companies requires navigating dense financial statements—Income Statements, Balance Sheets, and Cash Flow Statements—across multiple fiscal years and quarters. Traditional methods (spreadsheets, manual lookups) are slow, error-prone, and inaccessible to non-experts.

Large Language Models (LLMs) can summarize and explain complex data, but they suffer from a critical flaw: **hallucination**. An LLM might confidently fabricate revenue figures or invent ratios that don't exist in any source document.

### 1.2 Motivation

This project addresses two key challenges:

1. **Data Retrieval**: How do we programmatically fetch, normalize, and store structured financial data from public sources?
2. **Grounded Generation**: How do we leverage LLMs to answer questions while strictly preventing fabrication?

The answer is **Retrieval-Augmented Generation (RAG)**—a hybrid approach where the LLM is given *only* the relevant retrieved data, and is instructed to refuse answers if sufficient data is unavailable.

### 1.3 High-Level Features

| Feature | Description |
|---------|-------------|
| **Multi-Statement Support** | Income Statement, Balance Sheet, Cash Flow Statement (Annual & Quarterly) |
| **Temporal Awareness** | Supports queries like "Revenue in FY2022" or "Q3 2024 profit" |
| **Strict Governance** | Zero hallucinations—mandatory citations, refusal on missing data |
| **Hybrid Retrieval** | SQL (for exact numbers) + Vector Search (for semantic matching) |
| **Rate-Limit Resilience** | Graceful handling of API throttling with retries and fallbacks |

---

## 2. System Architecture

### 2.1 Overall Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              WEB UI (HTML/CSS/JS)                       │
│                          [http://localhost:8000]                        │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP POST /api/v1/query
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  1. API Routes: /ingest/company, /query/, /health/               │  │
│  │  2. Dependency Injection: Database Session (AsyncSession)        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│ IngestionService│      │  HybridRetriever    │      │   LLMService    │
│  (Data Pipeline)│      │  (Query Routing)    │      │  (Answer Gen)   │
└────────┬────────┘      └──────────┬──────────┘      └────────┬────────┘
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│ Yahoo Finance   │      │ QueryClassifier     │      │  Groq LLM API   │
│ (yfinance lib)  │      │ (Numeric/Factual)   │      │ (llama-3.1-8b)  │
└─────────────────┘      └──────────┬──────────┘      └─────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
           ┌─────────────────┐             ┌─────────────────┐
           │  SQLRetriever   │             │  VectorStore    │
           │  (PostgreSQL)   │             │  (ChromaDB)     │
           └─────────────────┘             └─────────────────┘
```

### 2.2 Component Responsibilities

| Component | File(s) | Responsibility |
|-----------|---------|----------------|
| **Web UI** | `static/index.html, script.js, style.css` | User interface for ingestion and querying |
| **FastAPI App** | `app/main.py`, `app/api/routes/` | HTTP routing, request validation |
| **Ingestion Service** | `app/ingestion/*.py` | Fetch → Normalize → Store pipeline |
| **Hybrid Retriever** | `app/retrieval/hybrid_retriever.py` | Routes queries to SQL or Vector retriever |
| **Query Classifier** | `app/retrieval/query_classifier.py` | LLM-based classification (Numeric/Factual/Hybrid) |
| **SQL Retriever** | `app/retrieval/sql_retriever.py` | Keyword + year-based SQL queries |
| **Vector Store** | `app/core/vector_store.py` | ChromaDB wrapper for semantic search |
| **LLM Service** | `app/llm/llm_service.py` | Groq API integration with strict prompting |
| **Prompt Templates** | `app/llm/prompt_templates.py` | Anti-hallucination governance rules |

### 2.3 Data Flow: Query to Answer

1. **User Query**: "What is the revenue for INFY.NS?"
2. **FastAPI** receives the request at `/api/v1/query/`
3. **QueryClassifier** uses a lightweight LLM call to classify: → `NUMERIC`
4. **HybridRetriever** routes to **SQLRetriever** (since it's numeric)
5. **SQLRetriever** queries PostgreSQL:
   - Extracts keywords: `["revenue", "sales", "turnover", "income", "earnings", "infy"]`
   - Finds matching `FinancialLineItem` rows (e.g., "Total Revenue", "Operating Revenue")
6. **Context Builder** formats results:
   ```
   === STRUCTURED FINANCIAL DATA (High Confidence) ===
   - Operating Revenue: 5,076,000,000.0 (FY2025 Q3, income_statement)
   - Total Revenue: 5,076,000,000.0 (FY2025 Q3, income_statement)
   ```
7. **LLMService** invokes Groq with the context and strict prompt
8. **Response**: "The Operating Revenue for INFY.NS in FY2025 Q3 is ₹5,076,000,000. [Source: FY2025 Q3, Income Statement]"

---

## 3. Technologies and Models

### 3.1 Technology Stack

| Layer | Technology | Why This Choice |
|-------|------------|-----------------|
| **Language** | Python 3.10+ | Mature ecosystem for ML/AI, async support |
| **Web Framework** | FastAPI | High performance, native async, auto-docs |
| **Database** | PostgreSQL + SQLAlchemy | Robust relational DB, async support via `asyncpg` |
| **Vector Store** | ChromaDB | Lightweight, embedded, works locally |
| **LLM Provider** | Groq API | Blazing-fast inference (14k requests/day free tier) |
| **Data Source** | Yahoo Finance (`yfinance`) | Free, comprehensive financial data |
| **Retry Logic** | Tenacity | Production-grade retry with exponential backoff |

### 3.2 LLM Models

| Purpose | Model | Rationale |
|---------|-------|-----------|
| **Query Classification** | `llama-3.1-8b-instant` | Fast, cheap, sufficient for simple classification |
| **Answer Generation** | `llama-3.1-8b-instant` | Good balance of speed, accuracy, and rate limits |

**Why Groq over OpenAI/Gemini?**
- **Speed**: Groq uses custom LPU hardware, delivering near-instant responses
- **Cost**: Free tier allows 14,400 requests/day (vs ~1,000 for larger models)
- **Rate Limits**: The 8B model is much less likely to hit rate limits

**Design Decision**: We initially used `llama-3.3-70b-versatile` but switched to `llama-3.1-8b-instant` after encountering frequent 429 (Rate Limit) errors on the free tier.

### 3.3 Embedding Model

| Component | Model | Dimensions |
|-----------|-------|------------|
| **ChromaDB** | `sentence-transformers/all-MiniLM-L6-v2` | 384 |

This model is compact, fast, and suitable for semantic similarity over short text chunks.

---

## 4. RAG Pipeline

### 4.1 Step-by-Step Flow

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ User Query    │───▶│ Query         │───▶│ Retrieval     │───▶│ Context       │───▶│ LLM           │
│               │    │ Understanding │    │ (SQL/Vector)  │    │ Construction  │    │ Generation    │
└───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
     "Revenue?"         NUMERIC              SQL Query           Formatted          "Revenue is X"
                        Classification       Results             Context String     + Citation
```

### 4.2 Query Understanding (Classification)

The **QueryClassifier** uses the LLM to categorize queries:

| Type | Example | Retrieval Strategy |
|------|---------|-------------------|
| `NUMERIC` | "What is the revenue?" | SQL only |
| `FACTUAL` | "What does the company do?" | Vector only |
| `HYBRID` | "Why did profit drop?" | SQL + Vector |
| `GENERAL` | "What is a stock?" | LLM knowledge (no retrieval) |

**Implementation** (`app/retrieval/query_classifier.py`):
```python
self.prompt = ChatPromptTemplate.from_messages([
    ("system", """Classify the query into: numeric, factual, hybrid, or general.
    Output JSON: {"query_type": "...", "reasoning": "..."}"""),
    ("human", "{query}"),
])
```

### 4.3 Retrieval

#### SQL Retrieval (Structured Data)

**Keyword Extraction**: The query is parsed to extract financial terms using a synonym mapping:

```python
self.financial_term_mappings = {
    "revenue": ["revenue", "sales", "turnover", "income", "earnings"],
    "profit": ["profit", "income", "earnings", "pbt", "pat"],
    "assets": ["assets", "asset"],
    "liabilities": ["liabilities", "liability", "debt"],
    "capex": ["capital expenditure", "capex", "capital spending"],
    # ... more mappings
}
```

**Year Extraction**: Regex patterns find fiscal years:
- `FY22`, `FY 2022` → 2022
- `2023`, `2024` → Exact year

**SQL Query**:
```sql
SELECT line_item_name, line_item_value, fiscal_year, statement_type
FROM financial_line_items
JOIN financial_statements ON ...
WHERE company_id = ? AND (line_item_name ILIKE '%revenue%' OR ...)
AND fiscal_year = 2024
ORDER BY period_date DESC LIMIT 60;
```

#### Vector Retrieval (Semantic Search)

For factual queries, ChromaDB performs similarity search:
```python
results = collection.query(
    query_texts=["What is the business model?"],
    n_results=5,
    where={"ticker": "INFY.NS"}
)
```

**Note**: In the current implementation, vector retrieval returns 0 results for most queries because the ingestion pipeline only stores numerical line items as text chunks. Qualitative data (10-K text, risk factors, news) is not currently ingested.

### 4.4 Chunking Strategy

**Challenge**: Financial statements are tabular. Traditional text chunking would destroy structure.

**Solution**: **Per-Line-Item Chunking**

Each financial line item becomes a single chunk with full context:
```
Company: Infosys Ltd (INFY.NS)
Period: 2024-12-31 (quarterly)
Statement: income_statement
Line Item: Operating Revenue
Value: 5,076,000,000.00
```

**Advantages**:
1. Precise retrieval: "Revenue?" matches only revenue chunks
2. Metadata filtering: Filter by ticker, year, statement type
3. LLM-friendly: Each chunk is self-contained

### 4.5 Context Construction

The **HybridRetriever** merges SQL and Vector results into a formatted string:

```
=== STRUCTURED FINANCIAL DATA (High Confidence) ===
- Operating Revenue: 5,076,000,000.0 (FY2025 Q3, income_statement)
- Total Revenue: 5,076,000,000.0 (FY2025 Q3, income_statement)
- Net Income: 200,000,000.0 (FY2025 Q3, income_statement)

=== TEXTUAL CONTEXT FRAGMENTS ===
(Currently empty — no qualitative data ingested)
```

### 4.6 Handling Missing/Low-Relevance Documents

**Empty Retrieval**:
```python
if not context.strip():
    return "Cannot determine from available data."
```

**Low Confidence**: The prompt instructs the LLM:
> "If (and ONLY if) the required information is not found even after checking synonyms, respond with: 'Cannot determine from available data.'"

---

## 5. Reliability and Rate-Limiting Handling

### 5.1 Rate Limit Strategy

**Problem**: Free-tier LLM APIs aggressively throttle requests. A single 429 error could crash the user experience.

**Solution**: Multi-layer defense:

#### Layer 1: Tenacity Retry with Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def _execute_chain(self, query: str):
    return await self.chain.ainvoke({"query": query})
```

**Behavior**: If a request fails, retry up to 5 times with delays of 4s, 8s, 16s... (capped at 10s).

#### Layer 2: Graceful Error Messages

```python
except RetryError as e:
    return ("**System Notice**: The AI model is currently experiencing high traffic. "
            "Please wait a minute and try again.")
```

Users never see raw tracebacks.

#### Layer 3: Model Selection

We switched from `llama-3.3-70b-versatile` (1,000 req/day limit) to `llama-3.1-8b-instant` (14,400 req/day limit).

**Trade-off**: Slightly less sophisticated reasoning, but vastly more reliable for continuous use.

### 5.2 Caching (Future Work)

Currently, there is no caching layer. Potential improvements:
- **LRU Cache**: Cache identical query+ticker combinations
- **Redis**: Distributed cache for multi-instance deployments
- **Stale-While-Revalidate**: Serve cached data while refreshing in background

---

## 6. Financial Data Use Case (INFY.NS Example)

### 6.1 Data Sources

| Source | Data Type | Coverage |
|--------|-----------|----------|
| `yfinance` | Balance Sheet, Income Statement, Cash Flow | 4-5 years (Annual + Quarterly) |
| Yahoo Finance API | Company metadata (name, sector, industry) | Real-time |

**Assumption**: Data is in INR (Indian Rupees) for NSE/BSE tickers. The system does not perform currency conversion.

### 6.2 Data Extraction and Normalization

**Raw Data** (from `yfinance`):
```python
{
    "income_statement": {
        "annual": {
            "2024-03-31": {"Total Revenue": 1234000000, "Net Income": 567000000, ...},
            "2023-03-31": {...}
        },
        "quarterly": {...}
    }
}
```

**Normalized Output** (stored in PostgreSQL):

| Table | Fields |
|-------|--------|
| `companies` | id, ticker, name, sector, industry |
| `financial_statements` | id, company_id, statement_type, period_type, fiscal_year, fiscal_quarter, period_date |
| `financial_line_items` | id, statement_id, line_item_name, line_item_value, currency |

### 6.3 Validation

The **DataValidator** checks for:
- Missing critical fields (e.g., Total Revenue)
- Negative values where unexpected
- Extreme outliers (> 10x historical median)

Warnings are logged but do not block ingestion (non-critical flow).

### 6.4 Example Queries and Responses

| Query | Response |
|-------|----------|
| "What is the revenue for INFY.NS?" | "The Operating Revenue for INFY.NS in FY2025 Q3 is ₹5,076,000,000. [Source: FY2025 Q3, Income Statement]" |
| "What is the Net Profit?" | "The Net Income for INFY.NS is ₹200,000,000 for FY2025 Q3. [Source: FY2025 Q3, Income Statement]" |
| "Total Assets?" | "The Total Assets for INFY.NS are ₹X. [Source: FY2025 Q3, Balance Sheet]" |
| "What are the key risks?" | "Cannot determine from available data." (No qualitative text ingested) |
| "Will the stock go up?" | "Cannot determine from available data." (Speculation refused) |

---

## 7. Evaluation and Limitations

### 7.1 Evaluation Criteria

| Criterion | How We Measure |
|-----------|---------------|
| **Accuracy** | Does the numeric value match the database? (Manual spot-checks) |
| **Relevance** | Does the answer address the user's question? (Subjective review) |
| **Hallucination Control** | Does the LLM fabricate data? (Compare response to retrieved context) |
| **Citation Compliance** | Does every factual claim include `[Source: ...]`? |

### 7.2 Known Limitations

| Limitation | Impact | Potential Fix |
|------------|--------|---------------|
| **No Qualitative Data** | Cannot answer "What are the risks?" or "Business strategy?" | Ingest 10-K/annual report PDFs |
| **Yahoo Finance Coverage** | Some smaller companies have incomplete data | Add fallback to alternate APIs |
| **Rate Limits** | Heavy usage may still hit 429 errors | Upgrade to paid tier or add caching |
| **Single Company per Query** | Cannot compare across companies in one query | Enhance retriever to accept multiple tickers |
| **English Only** | UI and responses are English | Add i18n support |
| **Currency Hardcoded** | Assumes INR; no conversion | Add forex lookup |

### 7.3 Future Work

1. **Ingest Qualitative Data**: Parse 10-K PDFs, earnings call transcripts
2. **Multi-Company Comparison**: "Compare TCS vs INFY revenue"
3. **Chart Generation**: Visualize trends over time
4. **Fine-Tuned Classifier**: Train a smaller model for query classification (reduce LLM calls)
5. **User Authentication**: Track query history per user
6. **Streaming Responses**: Use SSE for real-time answer generation

---

## 8. Conclusion

### 8.1 Summary

This Financial RAG system demonstrates how to combine:
- **Structured Data Retrieval** (SQL) for precise numeric answers
- **Semantic Search** (Vector DB) for flexible query matching
- **LLM Generation** with strict anti-hallucination governance

The result is an AI assistant that can reliably answer financial questions about publicly traded Indian companies, always citing its sources and refusing to speculate.

### 8.2 Real-World Applications

| Application | Description |
|-------------|-------------|
| **Equity Research** | Analysts can quickly pull key metrics without manual lookups |
| **Due Diligence** | Investors can verify financial health before investment |
| **Academic Projects** | Students can explore RAG architecture with a working example |
| **Internal Dashboards** | Companies can build internal Q&A tools over proprietary data |

### 8.3 Key Takeaways

1. **RAG is not just "LLM + Search"**: The quality of retrieval, context construction, and prompt engineering determines success.
2. **Hallucination prevention requires multiple layers**: Prompt rules, temperature control, and context validation.
3. **Rate limits are a real production concern**: Always design for graceful degradation.
4. **Structured data in RAG is underexplored**: Most RAG tutorials focus on text; SQL retrieval is just as powerful.

---

## Appendix: File Reference

| Component | Path | Description |
|-----------|------|-------------|
| Entry Point | `run.py` | Starts Uvicorn server |
| FastAPI App | `app/main.py` | Application factory, route mounting |
| API Routes | `app/api/routes/` | `/ingest`, `/query`, `/health` endpoints |
| Database Config | `app/core/database.py` | Async SQLAlchemy engine |
| Models | `app/models/models.py` | Company, FinancialStatement, FinancialLineItem |
| Ingestion | `app/ingestion/` | Data fetching, normalization, validation |
| Retrieval | `app/retrieval/` | Classifier, SQL retriever, Vector store |
| LLM Service | `app/llm/llm_service.py` | Groq integration, answer generation |
| Prompt | `app/llm/prompt_templates.py` | Anti-hallucination rules |
| Web UI | `static/` | HTML, CSS, JavaScript |

---

*Document generated for academic/professional review. For the latest code, see the [GitHub Repository](https://github.com/sital-tharu/RAG_fastAPI).*
