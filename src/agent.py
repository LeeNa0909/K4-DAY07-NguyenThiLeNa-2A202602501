from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)
        return self.answer_from_results(question, results)

    def answer_from_results(self, question: str, results: list[dict]) -> str:
        """Answer using the exact chunks selected by a benchmark or caller."""
        context = "\n\n".join(
            f"[{index}] {result['content']}"
            for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Answer the question using only the context below. "
            "If the context does not contain the answer, say that the information is unavailable.\n\n"
            f"Context:\n{context or '(no relevant documents)'}\n\n"
            f"Question: {question}\nAnswer:"
        )
        return self.llm_fn(prompt)
