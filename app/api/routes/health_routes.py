from fastapi import APIRouter
from app.api.schemas import HealthResponse

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", version="1.0.0")
