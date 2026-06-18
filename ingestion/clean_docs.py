import json
import re
from pathlib import Path

RAW_DIR = Path("data/raw/kubernetes")
OUT_FILE = Path("data/processed/cleaned_docs.jsonl")


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter delimited by --- at the start of the file."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :]
    return text


def clean_content(text: str) -> str:
    # Hugo shortcodes: {{< ... >}} and {{% ... %}}
    text = re.sub(r"\{\{[<%].*?[>%]\}\}", "", text, flags=re.DOTALL)
    # HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Markdown images ![alt](url)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # Markdown links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    # Heading markers (## Heading → Heading)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold/italic: ***text***, **text**, *text*, __text__, _text_
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
    # Inline code `code` → code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Fenced code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_doc_id(path: Path) -> str:
    """
    Use the file stem as doc_id.
    For _index.md files, use the parent directory name.
    """
    if path.stem == "_index":
        return path.parent.name
    return path.stem


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
