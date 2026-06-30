CREATE TABLE IF NOT EXISTS chunks_recursive (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT        NOT NULL,
    chunk_index INT         NOT NULL,
    title       TEXT,
    source_path TEXT,
    url         TEXT,
    content     TEXT        NOT NULL,
    word_count  INT,
    char_count  INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks_semantic (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT        NOT NULL,
    chunk_index INT         NOT NULL,
    title       TEXT,
    source_path TEXT,
    url         TEXT,
    content     TEXT        NOT NULL,
    word_count  INT,
    char_count  INT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recursive_doc_id ON chunks_recursive (doc_id);
CREATE INDEX IF NOT EXISTS idx_semantic_doc_id  ON chunks_semantic  (doc_id);
