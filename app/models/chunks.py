from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ChunkBase(SQLModel):
    doc_id:      str
    chunk_index: int
    title:       Optional[str] = None
    source_path: Optional[str] = None
    url:         Optional[str] = None
    content:     str
    word_count:  Optional[int] = None
    char_count:  Optional[int] = None
    created_at:  Optional[datetime] = None


class ChunkRecursive(ChunkBase, table=True):
    __tablename__ = "chunks_recursive"
    chunk_id: str = Field(primary_key=True)


class ChunkSemantic(ChunkBase, table=True):
    __tablename__ = "chunks_semantic"
    chunk_id: str = Field(primary_key=True)
