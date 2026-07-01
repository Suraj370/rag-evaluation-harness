from openai import OpenAI
from qdrant_client import QdrantClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.models.chunks import ChunkRecursive, ChunkSemantic

EMBED_MODEL = "text-embedding-3-small"

STRATEGY_MODEL = {
    "recursive": ChunkRecursive,
    "semantic":  ChunkSemantic,
}

openai_client = OpenAI(api_key=settings.openai_api_key)
qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def embed_query(query: str) -> list[float]:
    response = openai_client.embeddings.create(input=[query], model=EMBED_MODEL)
    return response.data[0].embedding


def retrieve(query: str, strategy: str = "recursive", top_k: int = 5) -> list[dict]:
    model_cls = STRATEGY_MODEL[strategy]

    vector = embed_query(query)
    result = qdrant.query_points(
        collection_name=f"chunks_{strategy}",
        query=vector,
        limit=top_k,
        with_payload=True,
    )

    hits = result.points
    chunk_ids = [hit.payload["chunk_id"] for hit in hits]
    scores = {hit.payload["chunk_id"]: hit.score for hit in hits}

    with Session(engine) as session:
        rows = session.exec(
            select(model_cls).where(model_cls.chunk_id.in_(chunk_ids))
        ).all()

    row_map = {row.chunk_id: row for row in rows}

    return [
        {
            "chunk_id": chunk_id,
            "doc_id":   row_map[chunk_id].doc_id,
            "title":    row_map[chunk_id].title,
            "url":      row_map[chunk_id].url,
            "content":  row_map[chunk_id].content,
            "score":    round(scores[chunk_id], 4),
        }
        for chunk_id in chunk_ids
        if chunk_id in row_map
    ]
