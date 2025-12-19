from enum import Enum
from typing import List

class QueryType(Enum):
    NUMERIC = "numeric"
    FACTUAL = "factual"
    HYBRID = "hybrid"

class QueryClassifier:
    
    NUMERIC_KEYWORDS = {
        "growth", "increase", "decrease", "margin", "ratio", "profit", 
        "revenue", "earnings", "net income", "sales", "turnover", 
        "ebitda", "debt", "liability", "asset", "equity", "percent", "%",
        "yoy", "qoq", "compare", "difference", "total", "sum"
    }
    
    FACTUAL_KEYWORDS = {
        "what is", "who is", "describe", "explain", "summary", "summarize",
        "management", "risk", "competitor", "strategy", "outlook", "guidance",
        "segment", "product", "service", "history", "founded", "ceo", "board"
    }

    def classify(self, query: str) -> QueryType:
        """
        Classifies the query into a QueryType based on keywords.
        Simple heuristic approach.
        """
        query_lower = query.lower()
        
        has_numeric = any(kw in query_lower for kw in self.NUMERIC_KEYWORDS)
        has_factual = any(kw in query_lower for kw in self.FACTUAL_KEYWORDS)
        
        if has_numeric and has_factual:
            return QueryType.HYBRID
        elif has_numeric:
            return QueryType.NUMERIC
        elif has_factual:
            return QueryType.FACTUAL
        else:
            # Default to Hybrid if unsure, to be safe
            return QueryType.HYBRID
