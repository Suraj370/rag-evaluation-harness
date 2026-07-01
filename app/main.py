from fastapi import FastAPI

from app.api.routes import health, retrieve

app = FastAPI(title="RAG Evaluation Harness", version="0.1.0")

app.include_router(health.router)
app.include_router(retrieve.router)
