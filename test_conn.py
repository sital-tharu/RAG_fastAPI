import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import traceback

# Hardcoded for testing to verify driver
DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

async def test_connection():
    try:
        print(f"Connecting to {DATABASE_URL}...")
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            print("Connection successful!")
            result = await conn.execute("SELECT 1")
            print(f"Query result: {result.scalar()}")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
