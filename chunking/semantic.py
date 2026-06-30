import json
import os
import re
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

IN_FILE = Path("data/processed/normalized_docs.jsonl")
OUT_FILE = Path("data/processed/chunks_semantic.jsonl")

EMBED_MODEL = "text-embedding-3-small"
BUFFER_SIZE = 1           # sentences on each side for context window
BREAKPOINT_PERCENTILE = 95  # distances above this percentile become chunk boundaries
MAX_CHUNK_CHARS = 2000    # safety cap

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s.strip()]


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(input=texts, model=EMBED_MODEL)
    return [item.embedding for item in response.data]


def cosine_distance(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_chunks(sentences: list[str], embeddings: list[list[float]]) -> list[str]:
    if len(sentences) == 1:
        return sentences

    # Build context-window embeddings by averaging the buffer around each sentence
    context = []
    for i in range(len(sentences)):
        start = max(0, i - BUFFER_SIZE)
        end = min(len(sentences), i + BUFFER_SIZE + 1)
        window = np.array(embeddings[start:end])
        context.append(window.mean(axis=0))

    # Cosine distance between adjacent context windows
    distances = [cosine_distance(context[i], context[i + 1]) for i in range(len(context) - 1)]

    threshold = np.percentile(distances, BREAKPOINT_PERCENTILE)
    breakpoints = [i for i, d in enumerate(distances) if d > threshold]

    # Group sentences at breakpoints
    chunks, start = [], 0
    for bp in breakpoints:
        chunk = " ".join(sentences[start : bp + 1]).strip()
        if chunk:
            chunks.append(chunk)
        start = bp + 1
    tail = " ".join(sentences[start:]).strip()
    if tail:
        chunks.append(tail)

    # Safety: hard-split any chunk exceeding MAX_CHUNK_CHARS
    final = []
    for chunk in chunks:
        if len(chunk) <= MAX_CHUNK_CHARS:
            final.append(chunk)
        else:
            words, sub, sub_len = chunk.split(), [], 0
            for word in words:
                sub.append(word)
                sub_len += len(word) + 1
                if sub_len >= MAX_CHUNK_CHARS:
                    final.append(" ".join(sub))
                    sub, sub_len = [], 0
            if sub:
                final.append(" ".join(sub))

    return final


def chunk_doc(content: str) -> list[str]:
    sentences = split_sentences(content)
    if not sentences:
        return []
    embeddings = embed_batch(sentences)
    return build_chunks(sentences, embeddings)


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with IN_FILE.open(encoding="utf-8") as f_in, OUT_FILE.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            try:
                chunks = chunk_doc(doc["content"])
            except Exception as e:
                print(f"Skipping {doc['doc_id']}: {e}")
                continue

            for i, content in enumerate(chunks):
                record = {
                    "chunk_id": f"{doc['doc_id']}_{i}",
                    "doc_id": doc["doc_id"],
                    "chunk_index": i,
                    "strategy": "semantic",
                    "title": doc["title"],
                    "source_path": doc["source_path"],
                    "url": doc["url"],
                    "content": content,
                    "word_count": len(content.split()),
                    "char_count": len(content),
                }
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                written += 1

    print(f"Wrote {written} chunks to {OUT_FILE}")


if __name__ == "__main__":
    main()
