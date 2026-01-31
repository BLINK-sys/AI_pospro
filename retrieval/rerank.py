"""
Рерайтинг результатов поиска: буст по совпадению ключевых слов запроса в названии товара.
Товары, в названии которых есть «холодильник», «кофемолка» и т.п., поднимаются выше.
"""
import logging
import re
from typing import Any, List

logger = logging.getLogger(__name__)

# Слова запроса, которые не считаем типом товара (фильтры, предлоги, числа)
STOPWORDS = {
    "до", "для", "тысяч", "тыс", "бюджет", "млн", "миллион", "от", "и", "в", "на", "с", "по", "не",
    "что", "какой", "какая", "какие", "нужен", "нужна", "нужно", "хочу", "ищу", "подскажите",
    "кофейни", "кофейня", "кофе", "магазин", "руб", "тг", "тенге",
}


def _extract_product_terms(query: str) -> List[str]:
    """Извлекает из запроса слова, похожие на тип товара (холодильник, кофемолка и т.д.)."""
    text = re.sub(r"[^\w\s]", " ", query.lower())
    words = text.split()
    terms = []
    for w in words:
        w = w.strip()
        if len(w) >= 4 and w not in STOPWORDS and not w.isdigit():
            terms.append(w)
    return terms


def rerank(query: str, results: List[dict[str, Any]], top_k: int | None = None) -> List[dict[str, Any]]:
    """
    Переранжирование: товары, в названии которых есть ключевые слова запроса, поднимаются выше.
    """
    if not results:
        return []
    terms = _extract_product_terms(query)
    if not terms:
        out = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    else:
        # Сначала товары, в названии которых есть ключевое слово (холодильник, кофемолка и т.д.), затем по score
        out = sorted(
            results,
            key=lambda p: (
                -(1 if any(t in (p.get("name") or "").lower() for t in terms) else 0),
                -(p.get("score") or 0),
            ),
        )
    if top_k is not None:
        out = out[:top_k]
    return out
