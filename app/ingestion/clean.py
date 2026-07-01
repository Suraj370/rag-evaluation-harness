import html
import json
import re
from pathlib import Path

RAW_DIR = Path("data/raw/kubernetes")
OUT_FILE = Path("data/processed/cleaned_docs.jsonl")


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:]
    return text


def clean_content(text: str) -> str:
    text = re.sub(r"\{\{<\s*\w[^>]*>\}\}.*?\{\{<\s*/\w+\s*>\}\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\{[<%].*?[>%]\}\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\{#[^}]+\}", "", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\|[\s|:-]+\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|(.+)\|\s*$", lambda m: "  ".join(c.strip() for c in m.group(1).split("|")), text, flags=re.MULTILINE)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
    text = re.sub(r"(`{3,}|~{3,})[^\n]*\n.*?\1", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_doc_id(path: Path) -> str:
    relative = path.relative_to(RAW_DIR)
    if path.stem == "_index":
        parts = relative.parent.parts
        return "_".join(parts) if parts else "root"
    parts = relative.with_suffix("").parts
    return "_".join(parts)


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    md_files = sorted(RAW_DIR.rglob("*.md"))
    written = 0

    with OUT_FILE.open("w", encoding="utf-8") as out:
        for md_path in md_files:
            raw = md_path.read_text(encoding="utf-8")
            text = strip_frontmatter(raw)
            content = clean_content(text)
            if not content:
                continue
            doc_id = make_doc_id(md_path)
            record = {"doc_id": doc_id, "source_path": md_path.as_posix(), "content": content}
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written} documents to {OUT_FILE}")


if __name__ == "__main__":
    main()
