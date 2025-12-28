from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.retrieval.query_classifier import query_classifier, QueryType
from app.retrieval.sql_retriever import SQLRetriever
from app.core.vector_store import vector_store

class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Use singleton
        self.classifier = query_classifier
        self.sql_retriever = SQLRetriever(db)
        # Vector store matches implicit global instance or can be passed locally logic

    async def retrieve(self, ticker: str, query: str) -> Dict[str, Any]:
        """
        Perform hybrid retrieval based on query type.
        """
        print(f"DEBUG: [HybridRetriever] Starting retrieval for ticker={ticker}, query='{query}'", flush=True)
        query_type = await self.classifier.classify(query)
        print(f"DEBUG: [HybridRetriever] Classification Result: {query_type}", flush=True)
        
        sql_results = []
        vector_results = []
        
        print(f"DEBUG: [HybridRetriever] Starting SQL Retrieval...", flush=True)
        
        # SQL Retrieval (for Numeric or Hybrid)
        if query_type in [QueryType.NUMERIC, QueryType.HYBRID]:
            # Reduced limit to 30 to prevent OOM on Render Free Tier
            sql_data = await self.sql_retriever.retrieve_financial_data(ticker, query, limit=30)
            print(f"DEBUG: [HybridRetriever] SQL Retrieval done. Found {len(sql_data)} items.", flush=True)
            print(f"DEBUG: [HybridRetriever] SQL Retriever found {len(sql_data)} items")
            
            # Print breakdown of items found
            item_names = [d['line_item'] for d in sql_data]
            print(f"DEBUG: Items breakdown: {item_names[:10]} ...")
            if any("revenue" in name.lower() for name in item_names):
                print("DEBUG: ✅ 'Revenue' keyword found in retrieved data.")
            else:
                print("DEBUG: ❌ 'Revenue' NOT found in retrieved data!")
                
            sql_results.extend(sql_data)

        # Vector Retrieval (for Factual or Hybrid)
        if query_type in [QueryType.FACTUAL, QueryType.HYBRID]:
            print(f"DEBUG: [HybridRetriever] Starting Vector Retrieval...", flush=True)
            vector_data = await vector_store.similarity_search(
                query, 
                n_results=5, 
                filter={"ticker": ticker}
            )
            print(f"DEBUG: Vector Retriever found {len(vector_data)} items")
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
