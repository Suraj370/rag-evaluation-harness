import time

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlmodel import Session, select

from app.core.config import settings
from app.core.database import engine
from app.models.chunks import ChunkRecursive, ChunkSemantic

EMBED_MODEL = "text-embedding-3-small"
VECTOR_DIM = 1536
BATCH_SIZE = 100

STRATEGY_MODEL = {
    "chunks_recursive": ChunkRecursive,
    "chunks_semantic":  ChunkSemantic,
}

openai_client = OpenAI(api_key=settings.openai_api_key)
qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(name: str):
    existing = [c.name for c in qdrant.get_collections().collections]
    if name not in existing:
        qdrant.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        print(f"  Created collection: {name}")
    else:
        print(f"  Collection already exists: {name}")


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(input=texts, model=EMBED_MODEL)
    return [item.embedding for item in response.data]


def fetch_chunks(model_cls) -> list:
    with Session(engine) as session:
        return session.exec(
            select(model_cls).order_by(model_cls.doc_id, model_cls.chunk_index)
        ).all()


def index_collection(collection: str, model_cls):
    print(f"\nIndexing '{collection}' from PostgreSQL ...")
    ensure_collection(collection)
    chunks = fetch_chunks(model_cls)
    total = len(chunks)
    print(f"  Fetched {total:,} chunks from Postgres")

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i: i + BATCH_SIZE]
        vectors = embed_batch([c.content for c in batch])
        points = [
            PointStruct(
                id=i + j,
                vector=vectors[j],
                payload={
                    "chunk_id":    batch[j].chunk_id,
                    "doc_id":      batch[j].doc_id,
                    "title":       batch[j].title,
                    "url":         batch[j].url,
                    "source_path": batch[j].source_path,
                },
            )
            for j in range(len(batch))
        ]
        qdrant.upsert(collection_name=collection, points=points)
        print(f"  {min(i + BATCH_SIZE, total)}/{total} indexed", end="\r")
        if i + BATCH_SIZE < total:
            time.sleep(0.5)

    print(f"  Done — {total:,} chunks in '{collection}'          ")


def main():
    for collection, model_cls in STRATEGY_MODEL.items():
        index_collection(collection, model_cls)
    print("\nAll collections indexed.")


if __name__ == "__main__":
    main()
