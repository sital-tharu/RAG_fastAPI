
import asyncio
import sys
from app.core.database import AsyncSessionLocal
from app.retrieval.hybrid_retriever import HybridRetriever
from app.llm.llm_service import LLMService

# Set policy immediately for Windows compatibility with Psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    ticker = "RELIANCE.NS"
    query = "What is the total revenue of Reliance Industries in the latest fiscal year?"
    
    print(f"--- Testing RAG Query for {ticker} ---")
    print(f"Query: {query}")
    
    # 1. Initialize DB Session
    async with AsyncSessionLocal() as db:
        # 2. Retrieve Context (Hybrid: SQL + Vector)
        retriever = HybridRetriever(db)
        try:
            # Test SQL
            print("Testing SQL Retriever...")
            sql_data = await retriever.sql_retriever.retrieve_financial_data(ticker, query)
            print(f"SQL Result: Found {len(sql_data)} items")
            for item in sql_data:
                print(f"  - {item['line_item']} ({item['period']}, {item['statement']}) = {item['value']}")
            
            # Test Vector
            import sys
            if sys.platform == "win32":
                print("Skipping Vector Store Test (Windows - Stability)")
                vector_data = []
            else:
                print("Testing Vector Store...")
                from app.core.vector_store import vector_store
                vector_data = await vector_store.similarity_search(
                    query, 
                    n_results=5, 
                    filter={"ticker": ticker}
                )
                print(f"Vector Result: Found {len(vector_data)} items")
            
            
            retrieval_result = {
                "context_str": retriever._build_context_str(sql_data, vector_data)
            }
            print(f"FULL CONTEXT:\n{retrieval_result['context_str']}\n")
        except Exception as e:
            print(f"CRITICAL ERROR in retriever.retrieve: {e}")
            import traceback
            traceback.print_exc()
            return
        
        context_str = retrieval_result.get("context_str", "")
        print(f"\nContext Retrieved ({len(context_str)} chars):")
        print("-" * 20)
        print(context_str[:500] + "..." if len(context_str) > 500 else context_str)
        print("-" * 20)
        
        if not context_str:
            print("ERROR: No context retrieved. Check data ingestion.")
            return

        # 3. Generate Answer (LLM)
        llm_service = LLMService()
        print("\nSending to LLM (Gemini)...")
        try:
            answer = await llm_service.generate_answer(query, context_str)
            print("\n=== ANSWER ===")
            print(answer)
            print("==================")
        except Exception as e:
            print(f"\nERROR calling LLM: {e}")
            print("Verify your GOOGLE_API_KEY in .env")

if __name__ == "__main__":
    asyncio.run(main())
