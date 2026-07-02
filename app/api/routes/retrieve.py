from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.retrieval.pipeline import RetrievalPipeline

router = APIRouter()

# Create once and reuse for all requests
pipeline = RetrievalPipeline()


class RetrieveRequest(BaseModel):
    query: str
    strategy: str = "recursive"
    top_k: int = 20          # Number of candidates retrieved from Qdrant
    final_k: int = 5         # Number of chunks returned to the client
    reranker: bool = False   # Enable/disable reranking


class ChunkResult(BaseModel):
    chunk_id: str
    doc_id: str
    title: str | None
    url: str | None
    content: str
    score: float
    rerank_score: float | None = None


class RetrieveResponse(BaseModel):
    query: str
    strategy: str
    reranker: bool
    results: list[ChunkResult]


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_chunks(req: RetrieveRequest):
    # Validate strategy
    if req.strategy not in ("recursive", "semantic"):
        raise HTTPException(
            status_code=400,
            detail="strategy must be 'recursive' or 'semantic'",
        )

    # Validate top_k
    if not 1 <= req.top_k <= 50:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 50",
        )

    # Validate final_k
    if not 1 <= req.final_k <= req.top_k:
        raise HTTPException(
            status_code=400,
            detail="final_k must be between 1 and top_k",
        )

    results = pipeline.retrieve(
        query=req.query,
        strategy=req.strategy,
        top_k=req.top_k,
        final_k=req.final_k,
        use_reranker=req.reranker,
    )

    return RetrieveResponse(
        query=req.query,
        strategy=req.strategy,
        reranker=req.reranker,
        results=results,
    )