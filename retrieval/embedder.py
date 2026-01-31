"""
Эмбеддинги через sentence-transformers, нормализация для косинусного поиска (FAISS Inner Product).
"""
import logging
from typing import List

import numpy as np

from config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None

_model = None


def get_model():
    global _model
    if _model is None:
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers not installed. pip install sentence-transformers")
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def normalize(vectors: np.ndarray) -> np.ndarray:
    """Нормализация по строкам (L2). После этого Inner Product = cosine similarity."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return (vectors / norms).astype(np.float32)


class Embedder:
    """Эмбеддер с нормализацией."""

    def __init__(self, model_name: str | None = None):
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers not installed. pip install sentence-transformers")
        self.model = SentenceTransformer(model_name or EMBEDDING_MODEL)

    def embed(self, texts: List[str]) -> np.ndarray:
        """Тексты -> нормализованные векторы (n, dim)."""
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)  # MiniLM dim
        vectors = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=bool(len(texts) > 50))
        return normalize(vectors)

    def embed_query(self, query: str) -> np.ndarray:
        """Один запрос -> вектор (dim,) нормализованный."""
        v = self.model.encode([query], convert_to_numpy=True)
        return normalize(v)[0]
