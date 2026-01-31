"""
Поиск topK по индексу с фильтрами: цена, категория, бренд, наличие.
Поддержка обращённого порядка слов («холодильная витрина» и «витрина холодильная» дают один результат).
"""
import logging
import re
from typing import Any

from config import RETRIEVAL_TOP_K
from index.faiss_store import load_index, search
from retrieval.embedder import Embedder
from retrieval.filters import apply_filters

logger = logging.getLogger(__name__)

# Слова запроса, не несущие типа товара (для извлечения значимых слов)
_STOPWORDS = {
    "до", "для", "тысяч", "тыс", "бюджет", "млн", "миллион", "от", "и", "в", "на", "с", "по", "не",
    "какой", "какая", "какие", "нужен", "нужна", "нужно", "хочу", "ищу", "подскажите", "кофейни", "кофейня",
    "руб", "тг", "тенге", "цена", "стоимость", "примерно", "около",
}


def _query_terms(query: str) -> list[str]:
    """Извлекает значимые слова из запроса (для обращённого варианта)."""
    text = re.sub(r"[^\w\s]", " ", (query or "").lower())
    return [w for w in text.split() if len(w) >= 3 and w not in _STOPWORDS and not w.isdigit()]


def search_products(
    query: str,
    top_k: int = RETRIEVAL_TOP_K,
    *,
    price_min: float | None = None,
    price_max: float | None = None,
    category_id: int | None = None,
    category_ids: list[int] | None = None,
    brand_id: int | None = None,
    in_stock_only: bool = False,
) -> list[dict[str, Any]]:
    """
    Векторный поиск по запросу с фильтрами.
    category_ids — список id категории и подкатегорий (поиск внутри ветки).
    """
    index, meta = load_index()
    if index is None or not meta:
        logger.warning("Index not loaded, returning empty results")
        return []

    try:
        embedder = Embedder()
    except ImportError as e:
        logger.warning("Embedder not available: %s", e)
        return []
    qv = embedder.embed_query(query)
    has_filters = price_min or price_max or category_id or category_ids or brand_id or in_stock_only
    if category_ids:
        k_search = min(max(top_k * 50, 1500), index.ntotal)
    elif has_filters:
        k_search = min(top_k * 5, index.ntotal)
    else:
        k_search = top_k
    k_search = max(k_search, top_k)
    distances, indices = search(index, qv, k_search)
    indices_list = indices.tolist()
    scores_list = distances.tolist()

    # Обращённый порядок слов: «холодильная витрина» и «витрина холодильная» дают один объединённый результат
    terms = _query_terms(query)
    if len(terms) >= 2:
        query_reversed = " ".join(reversed(terms))
        if query_reversed != query.strip().lower():
            qv2 = embedder.embed_query(query_reversed)
            dist2, idx2 = search(index, qv2, k_search)
            idx2_list = idx2.tolist()
            scores2_list = dist2.tolist()
            by_idx: dict[int, float] = {}
            for i, idx in enumerate(indices_list):
                by_idx[idx] = max(by_idx.get(idx, 0), scores_list[i])
            for i, idx in enumerate(idx2_list):
                by_idx[idx] = max(by_idx.get(idx, 0), scores2_list[i])
            merged_idx = sorted(by_idx.keys(), key=lambda x: -by_idx[x])
            merged_scores = [by_idx[x] for x in merged_idx]
            indices_list = merged_idx
            scores_list = merged_scores

    use_category_id = category_id if not category_ids else None
    filtered_idx, filtered_scores = apply_filters(
        meta,
        indices_list,
        scores_list,
        price_min=price_min,
        price_max=price_max,
        category_id=use_category_id,
        category_ids=category_ids,
        brand_id=brand_id,
        in_stock_only=in_stock_only,
    )
    filtered_idx = filtered_idx[:top_k]
    filtered_scores = filtered_scores[:top_k]

    from config import FRONTEND_BASE_URL, BACKEND_BASE_URL

    results = []
    for idx, score in zip(filtered_idx, filtered_scores):
        m = meta[idx].copy()
        m["score"] = round(float(score), 4)
        m["url"] = f"{FRONTEND_BASE_URL}/product/{m['slug']}" if m.get("slug") else ""
        if m.get("image_url") and not m["image_url"].startswith("http"):
            m["image_url"] = f"{BACKEND_BASE_URL}{m['image_url']}"
        results.append(m)
    return results
