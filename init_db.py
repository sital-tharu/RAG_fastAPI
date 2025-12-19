import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from app.core.config import get_settings
from app.models.models import Base
from app.core.database import engine as app_engine

settings = get_settings()

async def create_database():
    """Create the database if it doesn't exist"""
    url_str = settings.DATABASE_URL
    if "postgresql+psycopg://" in url_str:
        clean_url = url_str.replace("postgresql+psycopg://", "postgresql://")
    elif "postgresql+asyncpg://" in url_str:
        clean_url = url_str.replace("postgresql+asyncpg://", "postgresql://")
    else:
        clean_url = url_str

    from urllib.parse import urlparse
    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip('/')
    
    # Connect to 'postgres' system database
    # Construct async driver URL for system DB
    # We need to use the same driver as configured (postgresql+psycopg)
    driver_prefix = settings.DATABASE_URL.split("://")[0]
    sys_url = f"{driver_prefix}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
    
    print(f"Checking if database '{db_name}' exists...")
    
    # Create a temporary engine for system operations with AUTOCOMMIT
    sys_engine = create_async_engine(sys_url, isolation_level="AUTOCOMMIT")
    
    try:
        async with sys_engine.connect() as conn:
            # Check if database exists
            from sqlalchemy import text
            result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            exists = result.scalar()
            
            if not exists:
                print(f"Database '{db_name}' does not exist. Creating...")
                await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error checking/creating database: {e}")
    finally:
        await sys_engine.dispose()

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
