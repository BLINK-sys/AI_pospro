"""
Определение категории по тексту запроса (холодильник → Холодильное оборудование и т.д.).
"""
import logging
import re
from typing import Any

from data_access.categories_loader import load_categories, get_children

logger = logging.getLogger(__name__)

# Слова запроса, не несущие типа товара
STOPWORDS = {
    "до", "для", "тысяч", "тыс", "бюджет", "млн", "миллион", "от", "и", "в", "на", "с", "по", "не",
    "какой", "какая", "какие", "нужен", "нужна", "нужно", "хочу", "ищу", "подскажите", "кофейни", "кофейня",
    "руб", "тг", "тенге", "цена", "стоимость", "примерно", "около",
}


def _normalize_word(w: str) -> str:
    return w.lower().strip()


def _query_terms(query: str) -> list[str]:
    text = re.sub(r"[^\w\s]", " ", query.lower())
    return [w for w in text.split() if len(w) >= 3 and w not in STOPWORDS and not w.isdigit()]


def _category_terms(name: str) -> list[str]:
    text = re.sub(r"[^\w\s]", " ", (name or "").lower())
    return [w for w in text.split() if len(w) >= 3]


def _words_match(qt: str, ct: str, min_prefix: int = 4) -> bool:
    """Совпадение по подстроке или по общему префиксу (холодильная/холодильное, витрина/витрины)."""
    if qt == ct:
        return True
    if qt in ct or ct in qt:
        return True
    if len(qt) >= min_prefix and len(ct) >= min_prefix and qt[:min_prefix] == ct[:min_prefix]:
        return True
    return False


def match_query_to_category(query: str) -> tuple[int | None, str | None, list[dict[str, Any]]]:
    """
    По запросу определяет наиболее подходящую категорию.
    Возвращает (category_id, category_name, children) или (None, None, []).
    При равном счёте предпочитается родительская категория (чтобы искать по всей ветке).
    """
    categories = load_categories()
    if not categories:
        return None, None, []

    q_terms = _query_terms(query)
    if not q_terms:
        return None, None, []

    # Счёт: сколько слов запроса совпадают со словами названия категории (или наоборот)
    scored: list[tuple[int, int, dict]] = []  # (score, is_parent, category)
    children_map: dict[int, list[int]] = {}
    for c in categories:
        pid = c.get("parent_id")
        if pid is not None:
            children_map.setdefault(pid, []).append(c["id"])

    for c in categories:
        c_terms = _category_terms(c["name"])
        if not c_terms:
            continue
        score = 0
        for qt in q_terms:
            for ct in c_terms:
                if _words_match(qt, ct):
                    score += 1
                    break
        if score > 0:
            is_parent = 1 if c["id"] in children_map else 0
            scored.append((score, is_parent, c))

    if not scored:
        return None, None, []

    # Сортируем: сначала по score (больше лучше), затем предпочитаем родителя (is_parent=1)
    scored.sort(key=lambda x: (-x[0], -x[1]))
    best = scored[0][2]
    cat_id = best["id"]
    cat_name = best["name"]
    children = get_children(cat_id, categories)
    return cat_id, cat_name, children
