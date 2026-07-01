import json
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

from app.core.database import engine, init_db
from app.models.chunks import ChunkRecursive, ChunkSemantic

BATCH_SIZE = 500

CHUNKS = {
    ChunkRecursive: Path("data/processed/chunks_recursive.jsonl"),
    ChunkSemantic:  Path("data/processed/chunks_semantic.jsonl"),
}


def load_table(model_cls, path: Path) -> int:
    rows = []
    seen = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            if c["chunk_id"] in seen:
                continue
            seen.add(c["chunk_id"])
            rows.append({
                "chunk_id":    c["chunk_id"],
                "doc_id":      c["doc_id"],
                "chunk_index": c["chunk_index"],
                "title":       c.get("title"),
                "source_path": c.get("source_path"),
                "url":         c.get("url"),
                "content":     c["content"],
                "word_count":  c.get("word_count"),
                "char_count":  c.get("char_count"),
            })

    inserted = 0
    with Session(engine) as session:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i: i + BATCH_SIZE]
            stmt = pg_insert(model_cls).values(batch).on_conflict_do_nothing(
                index_elements=["chunk_id"]
            )
            session.exec(stmt)
            session.commit()
            inserted += len(batch)
            print(f"  {inserted}/{len(rows)} inserted", end="\r")

    return inserted


def main():
    init_db()
    for model_cls, path in CHUNKS.items():
        table = model_cls.__tablename__
        if not path.exists():
            print(f"Skipping {table}: {path} not found")
            continue
        print(f"Loading {table} from {path} ...")
        n = load_table(model_cls, path)
        print(f"  Inserted {n:,} rows into {table}     ")
    print("Done.")


if __name__ == "__main__":
    main()
