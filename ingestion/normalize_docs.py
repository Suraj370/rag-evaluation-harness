import json
from pathlib import Path

IN_FILE = Path("data/processed/cleaned_docs.jsonl")
OUT_FILE = Path("data/processed/normalized_docs.jsonl")

_RAW_PREFIX = "data/raw/kubernetes/"
_DOCS_BASE = "https://kubernetes.io/docs/"


def make_title(doc_id: str) -> str:
    return doc_id.replace("-", " ").replace("_", " ").title()


def make_url(source_path: str) -> str:
    path = source_path
    if path.startswith(_RAW_PREFIX):
        path = path[len(_RAW_PREFIX):]
    p = Path(path)
    if p.stem == "_index":
        url_path = p.parent.as_posix() + "/"
    else:
        url_path = p.with_suffix("").as_posix() + "/"
    return _DOCS_BASE + url_path


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with IN_FILE.open(encoding="utf-8") as f_in, OUT_FILE.open("w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            content = doc["content"]
            normalized = {
                "doc_id": doc["doc_id"],
                "title": make_title(doc["doc_id"]),
                "source_path": doc["source_path"],
                "url": make_url(doc["source_path"]),
                "content": content,
                "word_count": len(content.split()),
                "char_count": len(content),
            }
            f_out.write(json.dumps(normalized, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written} documents to {OUT_FILE}")


if __name__ == "__main__":
    main()
