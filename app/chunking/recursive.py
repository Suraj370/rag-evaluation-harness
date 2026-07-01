import json
from pathlib import Path

IN_FILE = Path("data/processed/normalized_docs.jsonl")
OUT_FILE = Path("data/processed/chunks_recursive.jsonl")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
SEPARATORS = ["\n\n", "\n", ". ", " "]


def recursive_split(text: str, separators: list, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size or not separators:
        return [text.strip()] if text.strip() else []
    sep, *rest = separators
    parts = [p for p in text.split(sep) if p.strip()]
    pieces = []
    for part in parts:
        if len(part) <= chunk_size:
            pieces.append(part.strip())
        else:
            pieces.extend(recursive_split(part, rest, chunk_size))
    return pieces


def merge_with_overlap(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    i = 0
    while i < len(pieces):
        chunk_parts, length, j = [], 0, i
        while j < len(pieces) and length + len(pieces[j]) + 1 <= chunk_size:
            chunk_parts.append(pieces[j])
            length += len(pieces[j]) + 1
            j += 1
        if not chunk_parts:
            chunk_parts = [pieces[i]]
            j = i + 1
        chunks.append(" ".join(chunk_parts).strip())
        overlap_len, new_i = 0, j - 1
        while new_i > i and overlap_len < overlap:
            overlap_len += len(pieces[new_i]) + 1
            new_i -= 1
        i = max(i + 1, new_i + 1)
    return [c for c in chunks if c]


def chunk_doc(content: str) -> list[str]:
    pieces = recursive_split(content, SEPARATORS, CHUNK_SIZE)
    return merge_with_overlap(pieces, CHUNK_SIZE, CHUNK_OVERLAP)


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with IN_FILE.open(encoding="utf-8") as f_in, OUT_FILE.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            chunks = chunk_doc(doc["content"])
            for i, content in enumerate(chunks):
                record = {
                    "chunk_id":    f"{doc['doc_id']}_{i}",
                    "doc_id":      doc["doc_id"],
                    "chunk_index": i,
                    "strategy":    "recursive",
                    "title":       doc["title"],
                    "source_path": doc["source_path"],
                    "url":         doc["url"],
                    "content":     content,
                    "word_count":  len(content.split()),
                    "char_count":  len(content),
                }
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1

    print(f"Wrote {written} chunks to {OUT_FILE}")


if __name__ == "__main__":
    main()
