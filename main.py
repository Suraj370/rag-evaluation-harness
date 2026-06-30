from fastapi import FastAPI

app = FastAPI(title="RAG Evaluation Harness", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
