import subprocess
import sys
import time
from pathlib import Path

STEPS = [
    ("Clean docs",      ["app/ingestion/clean.py"]),
    ("Normalize docs",  ["app/ingestion/normalize.py"]),
    ("Recursive chunk", ["app/chunking/recursive.py"]),
    ("Semantic chunk",  ["app/chunking/semantic.py"]),
    ("Load PostgreSQL", ["app/indexing/postgres.py"]),
    ("Index Qdrant",    ["app/indexing/qdrant.py"]),
]


def run_step(name: str, script: list[str]) -> bool:
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    start = time.time()

    result = subprocess.run(
        [sys.executable] + script,
        cwd=Path(__file__).parent.parent,
    )

    elapsed = round(time.time() - start, 1)
    if result.returncode != 0:
        print(f"\n  FAILED in {elapsed}s — stopping pipeline.")
        return False

    print(f"\n  Done in {elapsed}s")
    return True


def main():
    print("Starting RAG pipeline...")
    total_start = time.time()

    for name, script in STEPS:
        if not run_step(name, script):
            sys.exit(1)

    total = round(time.time() - total_start, 1)
    print(f"\nPipeline complete in {total}s")


if __name__ == "__main__":
    main()
