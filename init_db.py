import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.models.models import Base
from app.core.database import engine as app_engine

settings = get_settings()

async def create_database():
    """Create the database if it doesn't exist"""
    # Parse the URL to get the base URL (without db name) and the db name
    # Assumption: DATABASE_URL format is postgresql+asyncpg://user:pass@host:port/dbname
    
    url_str = settings.DATABASE_URL
    if "postgresql+asyncpg://" in url_str:
        clean_url = url_str.replace("postgresql+asyncpg://", "postgres://")
    else:
        clean_url = url_str

    from urllib.parse import urlparse
    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip('/')
    
    # Connect to the default 'postgres' database to create the new DB
    sys_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
    
    print(f"Checking if database '{db_name}' exists...")
    
    try:
        conn = await asyncpg.connect(sys_url)
        # Check if database exists
        exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        
        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")
            
        await conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        print("Please ensure your PostgreSQL server is running and the credentials in .env are correct.")
        return

async def init_tables():
    """Create tables defined in SQLAlchemy models"""
    print("Creating tables...")
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

async def main():
    await create_database()
    await init_tables()

if __name__ == "__main__":
    asyncio.run(main())
