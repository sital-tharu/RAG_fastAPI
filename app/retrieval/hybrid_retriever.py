from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.retrieval.query_classifier import QueryClassifier, QueryType
from app.retrieval.sql_retriever import SQLRetriever
from app.core.vector_store import vector_store

class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.classifier = QueryClassifier()
        self.sql_retriever = SQLRetriever(db)
        # Vector store matches implicit global instance or can be passed locally logic

    async def retrieve(self, ticker: str, query: str) -> Dict[str, Any]:
        """
        Perform hybrid retrieval based on query type.
        """
        query_type = await self.classifier.classify(query)
        
        sql_results = []
        vector_results = []
        
        # SQL Retrieval (for Numeric or Hybrid)
        if query_type in [QueryType.NUMERIC, QueryType.HYBRID]:
            sql_data = await self.sql_retriever.retrieve_financial_data(ticker, query)
            sql_results.extend(sql_data)

        # Vector Retrieval (for Factual or Hybrid)
        if query_type in [QueryType.FACTUAL, QueryType.HYBRID]:
            vector_data = await vector_store.similarity_search(
                query, 
                n_results=5, 
                filter={"ticker": ticker}
            )
            vector_results.extend(vector_data)

        return {
            "query_type": query_type.value,
            "sql_results": sql_results,
            "vector_results": vector_results,
            "context_str": self._build_context_str(sql_results, vector_results)
        }

    def _build_context_str(self, sql_results: List[Dict], vector_results: List[Dict]) -> str:
        """Merge results into a formatted string for LLM"""
        context_parts = []
        
        if sql_results:
            context_parts.append("=== STRUCTURED FINANCIAL DATA (High Confidence) ===")
            for item in sql_results:
                context_parts.append(
                    f"- {item['line_item']}: {item['value']:,} ({item['period']}, {item['statement']})"
                )
            context_parts.append("")
            
        if vector_results:
            context_parts.append("=== TEXTUAL CONTEXT FRAGMENTS ===")
            for item in vector_results:
                text = item['text'].replace('\n', ' | ')
                context_parts.append(f"- {text}")
                
        return "\n".join(context_parts)
