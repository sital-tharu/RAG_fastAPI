import sys
import asyncio



import sys
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import get_settings
from app.api.routes import ingestion_routes, query_routes, health_routes

# Fix for Windows ProactorEventLoop policy with psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="RAG-based Financial QA System using PostgreSQL + Vector DB + Gemini",
    version="1.0.0",
    debug=settings.DEBUG
)

# Helpers for routes
app.include_router(ingestion_routes.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(query_routes.router, prefix="/api/v1/query", tags=["Query"])
app.include_router(health_routes.router, prefix="/api/v1/health", tags=["Health"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse('static/index.html')
