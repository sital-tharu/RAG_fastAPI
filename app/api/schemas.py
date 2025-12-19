from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Ingestion Schemas
class IngestRequest(BaseModel):
    ticker: str

class IngestResponse(BaseModel):
    status: str
    company: str
    statements: int
    chunks: int
    message: Optional[str] = None

# Query Schemas
class QueryRequest(BaseModel):
    query: str
    ticker: str

class SourceItem(BaseModel):
    source: Optional[str] = "unknown"
    line_item: Optional[str] = None
    value: Optional[float] = None
    period: Optional[str] = None
    statement: Optional[str] = None
    text: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    query_type: str
    confidence: str = "high" # Placeholder for now
    sources: List[Dict[str, Any]]

# Health Schema
class HealthResponse(BaseModel):
    status: str
    version: str
