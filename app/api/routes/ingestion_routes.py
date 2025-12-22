from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.ingestion.ingestion_service import IngestionService
from app.api.schemas import IngestRequest, IngestResponse

router = APIRouter()

@router.post("/company", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_company(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    """
    Ingest financial data for a specific company ticker (e.g., TCS.NS).
    Fetches from Yahoo Finance, stores to Postgres and Vector DB.
    """
    service = IngestionService(db)
    try:
        result = await service.ingest_company(request.ticker)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
            
        await db.commit()
            
        return IngestResponse(
            status="success",
            company=result.get("company", "Unknown"),
            statements=result.get("statements", 0),
            chunks=result.get("chunks", 0),
            calculated_ratios=result.get("calculated_ratios", 0),  # NEW
            validation=result.get("validation"),  # NEW
            message="Successfully ingested financial data"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
