"""
Хранение и поиск по векторному индексу.
Использует FAISS при наличии, иначе — numpy (brute-force), чтобы работало на Windows без faiss-cpu.
"""
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from config import FAISS_INDEX_PATH, META_PATH, INDEX_DIR

logger = logging.getLogger(__name__)

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None

# Для numpy-fallback храним векторы отдельно
VECTORS_NPY_PATH = INDEX_DIR / "vectors.npy"


class NumpyIndex:
    """Индекс на numpy: нормализованные векторы, поиск через dot product = cosine."""

    def __init__(self, vectors: np.ndarray):
        self.vectors = vectors.astype(np.float32)
        self.ntotal = vectors.shape[0]

    def search(self, query_vector: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        q = query_vector.astype(np.float32)
        k = min(k, self.ntotal)
        scores = np.dot(q, self.vectors.T)[0]
        if k >= self.ntotal:
            idx = np.argsort(scores)[::-1]
            return scores[idx], idx
        idx = np.argpartition(-scores, k)[:k]
        idx = idx[np.argsort(-scores[idx])]
        return scores[idx], idx


def ensure_index_dir() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def add_vectors(vectors: np.ndarray, meta: list[dict[str, Any]]):
    """
    Создаёт индекс из векторов (нормализованы для cosine).
    Возвращает faiss.IndexFlatIP или NumpyIndex.
    """
    if len(vectors) != len(meta):
        raise ValueError("vectors and meta length mismatch")
    if HAS_FAISS:
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors.astype(np.float32))
        return index
    return NumpyIndex(vectors)


def search(index, query_vector: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Поиск top-k. index — faiss.IndexFlatIP или NumpyIndex."""
    if HAS_FAISS and hasattr(index, "ntotal") and not isinstance(index, NumpyIndex):
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        query_vector = query_vector.astype(np.float32)
        distances, indices = index.search(query_vector, min(k, index.ntotal))
        return distances[0], indices[0]
    return index.search(query_vector, k)


def save_index(index, meta: list[dict[str, Any]]) -> None:
    """Сохраняет индекс и метаданные."""
    ensure_index_dir()
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    if HAS_FAISS and hasattr(index, "ntotal") and not isinstance(index, NumpyIndex):
        faiss.write_index(index, str(FAISS_INDEX_PATH))
        logger.info("Saved FAISS index (%d vectors) and meta to %s", index.ntotal, INDEX_DIR)
    else:
        np.save(str(VECTORS_NPY_PATH), index.vectors)
        logger.info("Saved numpy index (%d vectors) and meta to %s", index.ntotal, INDEX_DIR)


def load_index() -> tuple[Any, list[dict[str, Any]]]:
    """Загружает индекс и метаданные. Если файлов нет — (None, [])."""
    if not META_PATH.exists():
        logger.warning("Meta file not found at %s", META_PATH)
        return None, []
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    if HAS_FAISS and FAISS_INDEX_PATH.exists():
        index = faiss.read_index(str(FAISS_INDEX_PATH))
        if index.ntotal != len(meta):
            logger.warning("Index size %d != meta size %d", index.ntotal, len(meta))
        return index, meta
    if VECTORS_NPY_PATH.exists():
        vectors = np.load(str(VECTORS_NPY_PATH))
        index = NumpyIndex(vectors)
        if index.ntotal != len(meta):
            logger.warning("Vectors rows %d != meta size %d", index.ntotal, len(meta))
        return index, meta
    logger.warning("No index file found (faiss.index or vectors.npy)")
    return None, []
