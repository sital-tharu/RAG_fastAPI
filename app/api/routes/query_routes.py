from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.retrieval.hybrid_retriever import HybridRetriever
from app.llm.llm_service import LLMService
from app.api.schemas import QueryRequest, QueryResponse

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def query_financials(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Answer natural language questions about a company's financials.
    Uses Hybrid RAG (SQL + Vector) + Gemini LLM.
    """
    try:
        # 1. Retrieve Context
        retriever = HybridRetriever(db)
        retrieval_result = await retriever.retrieve(request.ticker, request.query)
        
        context_str = retrieval_result["context_str"]
        query_type = retrieval_result["query_type"]
        
        # 2. Generate Answer
        llm = LLMService()
        answer = await llm.generate_answer(request.query, context_str)
        
        # 3. Format Response
        # Merge sources for citation
        sources = []
        sources.extend(retrieval_result["sql_results"])
        sources.extend([{"text": r["text"], "source": "vector"} for r in retrieval_result["vector_results"]])
        
        return QueryResponse(
            answer=answer,
            query_type=query_type,
            sources=sources,
            confidence="high" if sources else "low"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
