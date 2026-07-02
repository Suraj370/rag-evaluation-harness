import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "app/models/Qwen3-Reranker-0.6B"


class Reranker:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.token_true_id = None
        self.token_false_id = None

    def _load(self):
        if self.model is not None:
            return
        print("Loading Qwen3-Reranker-0.6B...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, padding_side="left")
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16)
        self.model.eval()
        self.token_true_id  = self.tokenizer("yes", add_special_tokens=False).input_ids[0]
        self.token_false_id = self.tokenizer("no",  add_special_tokens=False).input_ids[0]
        print("Reranker loaded.")

    def _format(self, query: str, document: str) -> str:
        return (
            "<|im_start|>system\n"
            "Judge whether the Document meets the requirements based on the Query and the "
            "Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n"
            "<|im_start|>user\n"
            "<Instruct>: Given a web search query, retrieve relevant passages that answer the query.\n"
            f"<Query>: {query}\n"
            f"<Document>: {document}<|im_end|>\n"
            "<|im_start|>assistant\n"
            "<think>\n\n</think>\n\n"
        )

    def rerank(self, query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
        self._load()

        prompts = [self._format(query, c["content"]) for c in chunks]
        inputs = self.tokenizer(
            prompts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        with torch.no_grad():
            logits = self.model(**inputs).logits[:, -1, :]

        scores = torch.softmax(
            logits[:, [self.token_false_id, self.token_true_id]], dim=-1
        )[:, 1].tolist()

        ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

        result = []
        for chunk, score in ranked[:top_k]:
            chunk = dict(chunk)
            chunk["rerank_score"] = round(score, 4)
            result.append(chunk)

        return result
