import asyncio
import os
import sys
import traceback
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.retrieval.sql_retriever import SQLRetriever

# Fix for Windows ProactorEventLoop policy with psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def test_retrieval():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        retriever = SQLRetriever(session)
        ticker = "INFY.NS"
        query = "What is the revenue for INFY.NS?"
        
        print(f"Testing retrieval for '{ticker}' with query: '{query}'")
        try:
            results = await retriever.retrieve_financial_data(ticker, query)
            
            if not results:
                print("❌ No results retrieved!")
            else:
                print(f"✅ Retrieved {len(results)} items.")
                
                # Check for Revenue
                revenue_items = [r for r in results if "revenue" in r['line_item'].lower()]
                if revenue_items:
                    print(f"✅ Found {len(revenue_items)} Revenue items:")
                    for item in revenue_items[:5]:
                        print(f"   🎯 {item['line_item']}: {item['value']} ({item['period']}, {item['statement']})")
                else:
                    print("⚠️ WARNING: No 'Revenue' items found in retrieval results!")
                    
                print("\n--- First 5 Items Retrieved ---")
                for item in results[:5]: 
                    print(f"   - {item['line_item']}: {item['value']} ({item['period']}, {item['statement']})")
                    
        except Exception:
            with open("error_log.txt", "w") as f:
                traceback.print_exc(file=f)
            print("❌ Error occurred! details written to error_log.txt")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
