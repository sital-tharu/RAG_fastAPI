from fastapi import FastAPI
from app.core.config import get_settings
from app.api.routes import ingestion_routes, query_routes, health_routes

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

@app.get("/")
async def root():
    return {"message": "Financial RAG API is running. Check /docs for API documentation."}
