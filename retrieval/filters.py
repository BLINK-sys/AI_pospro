"""
Фильтрация результатов поиска по цене, категории, бренду, наличию.
Отдельный модуль без зависимостей от faiss — для тестов.
"""
from typing import Any


def apply_filters(
    meta: list[dict[str, Any]],
    indices: list[int],
    scores: list[float],
    *,
    price_min: float | None = None,
    price_max: float | None = None,
    category_id: int | None = None,
    category_ids: list[int] | None = None,
    brand_id: int | None = None,
    in_stock_only: bool = False,
) -> tuple[list[int], list[float]]:
    """Оставляет только те индексы, которые проходят фильтры; порядок по score сохраняется."""
    out_idx: list[int] = []
    out_scores: list[float] = []
    for i, idx in enumerate(indices):
        if idx < 0 or idx >= len(meta):
            continue
        m = meta[idx]
        if price_min is not None and (m.get("price") or 0) < price_min:
            continue
        if price_max is not None and (m.get("price") or 0) > price_max:
            continue
        if category_id is not None and m.get("category_id") != category_id:
            continue
        if category_ids is not None and m.get("category_id") not in category_ids:
            continue
        if brand_id is not None and m.get("brand_id") != brand_id:
            continue
        if in_stock_only and (m.get("quantity") or 0) <= 0:
            continue
        out_idx.append(idx)
        out_scores.append(scores[i])
    return out_idx, out_scores
