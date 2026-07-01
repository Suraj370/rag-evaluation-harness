from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.retrieval.retrieve import retrieve

router = APIRouter()


class RetrieveRequest(BaseModel):
    query: str
    strategy: str = "recursive"
    top_k: int = 5


class ChunkResult(BaseModel):
    chunk_id: str
    doc_id: str
    title: str | None
    url: str | None
    content: str
    score: float


class RetrieveResponse(BaseModel):
    query: str
    strategy: str
    results: list[ChunkResult]


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve_chunks(req: RetrieveRequest):
    if req.strategy not in ("recursive", "semantic"):
        raise HTTPException(status_code=400, detail="strategy must be 'recursive' or 'semantic'")
    if not 1 <= req.top_k <= 20:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 20")

    results = retrieve(req.query, strategy=req.strategy, top_k=req.top_k)
    return RetrieveResponse(query=req.query, strategy=req.strategy, results=results)
