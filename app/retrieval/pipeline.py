from app.retrieval.retriever import Retriever
from app.retrieval.reranker import Reranker


class RetrievalPipeline:

    def __init__(self):
        self.retriever = Retriever()
        self.reranker = Reranker()

    def retrieve(
        self,
        query: str,
        strategy: str = "recursive",
        top_k: int = 20,
        final_k: int = 5,
        use_reranker: bool = False,
    ):
        chunks = self.retriever.retrieve(
            query=query,
            strategy=strategy,
            top_k=top_k,
        )

        if use_reranker:
            return self.reranker.rerank(
                query=query,
                chunks=chunks,
                top_k=final_k,
            )

        return chunks[:final_k]