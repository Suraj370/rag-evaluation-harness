import json
import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

CHUNKS = {
    "chunks_recursive": Path("data/processed/chunks_recursive.jsonl"),
    "chunks_semantic":  Path("data/processed/chunks_semantic.jsonl"),
}

INSERT_SQL = """
    INSERT INTO {table} (
        chunk_id, doc_id, chunk_index, title, source_path, url,
        content, word_count, char_count
    ) VALUES %s
    ON CONFLICT (chunk_id) DO NOTHING
"""


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def load_table(cur, table: str, path: Path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            rows.append((
                c["chunk_id"],
                c["doc_id"],
                c["chunk_index"],
                c.get("title"),
                c.get("source_path"),
                c.get("url"),
                c["content"],
                c.get("word_count"),
                c.get("char_count"),
            ))

    psycopg2.extras.execute_values(
        cur, INSERT_SQL.format(table=table), rows, page_size=500
    )
    return len(rows)


def main():
    conn = get_conn()
    conn.autocommit = False
    cur = conn.cursor()

    for table, path in CHUNKS.items():
        if not path.exists():
            print(f"Skipping {table}: {path} not found")
            continue
        print(f"Loading {table} from {path} ...")
        n = load_table(cur, table, path)
        conn.commit()
        print(f"  Inserted {n:,} rows into {table}")

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
