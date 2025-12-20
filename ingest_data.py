
import asyncio
import sys
import traceback
from app.core.database import AsyncSessionLocal
from app.ingestion.ingestion_service import IngestionService

# Set policy immediately for Windows compatibility with Psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else "TCS.NS"
    print(f"Starting ingestion for {ticker}...")
    
    async with AsyncSessionLocal() as db:
        service = IngestionService(db)
        try:
            result = await service.ingest_company(ticker)
            
            if result.get("status") == "error":
                print(f"Error: {result.get('message')}")
            else:
                print("Ingestion Successful!")
                print(f"Company: {result.get('company')}")
                print(f"Statements Ingested: {result.get('statements')}")
                print(f"Chunks Created: {result.get('chunks')}")
                
            await db.commit()
            print("Transaction Committed.")
        except Exception as e:
            traceback.print_exc()
            print(f"Critical Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
