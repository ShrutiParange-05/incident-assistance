"""
Lightweight retrieval layer: TF-IDF + cosine similarity over the
runbook knowledge base.

This is intentionally not a vector-DB/embeddings setup — for a
knowledge base this small, TF-IDF is fast, has zero external service
dependency, and is easy to reason about. Swap this module for a real
embedding + vector store (pgvector, Pinecone, etc.) once the doc set
grows; nothing else in the pipeline needs to change since the public
surface is just `retrieve(query, top_k)`.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.rag.knowledge_base import all_documents


class Retriever:
    def __init__(self, documents: list[dict] | None = None):
        self.documents = documents if documents is not None else all_documents()
        corpus = [f"{d['title']} {' '.join(d['tags'])} {d['content']}" for d in self.documents]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.05) -> list[dict]:
        """Return the top_k most relevant documents for `query`, each with a similarity score."""
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()

        ranked = sorted(zip(self.documents, scores), key=lambda pair: pair[1], reverse=True)
        return [
            {**doc, "score": round(float(score), 4)}
            for doc, score in ranked[:top_k]
            if score >= min_score
        ]


# Module-level singleton — the vectorizer only needs to be fit once per process.
_retriever = Retriever()


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    return _retriever.retrieve(query, top_k=top_k)
