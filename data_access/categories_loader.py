"""
Загрузка дерева категорий из БД для определения категории по запросу и фильтрации.
"""
import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DATABASE_URL

logger = logging.getLogger(__name__)

_categories_cache: list[dict[str, Any]] | None = None
_children_map: dict[int, list[int]] | None = None


def get_engine() -> Engine:
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def load_categories(engine: Engine | None = None) -> list[dict[str, Any]]:
    """Загружает все категории: id, name, slug, parent_id."""
    global _categories_cache
    if _categories_cache is not None:
        return _categories_cache
    eng = engine or get_engine()
    sql = text("SELECT id, name, slug, parent_id FROM category ORDER BY parent_id NULLS FIRST, \"order\"")
    with eng.connect() as conn:
        rows = conn.execute(sql).fetchall()
    _categories_cache = [
        {"id": r.id, "name": r.name or "", "slug": r.slug or "", "parent_id": r.parent_id}
        for r in rows
    ]
    logger.info("Loaded %d categories", len(_categories_cache))
    return _categories_cache


def _build_children_map(categories: list[dict[str, Any]]) -> dict[int, list[int]]:
    """parent_id -> [child_id, ...]"""
    m: dict[int, list[int]] = {}
    for c in categories:
        pid = c.get("parent_id")
        if pid is not None:
            m.setdefault(pid, []).append(c["id"])
    return m


def get_descendant_ids(category_id: int, categories: list[dict[str, Any]] | None = None) -> list[int]:
    """Возвращает [category_id] + все id подкатегорий (рекурсивно)."""
    global _children_map
    cats = categories or load_categories()
    if _children_map is None:
        _children_map = _build_children_map(cats)
    result = [category_id]
    stack = [category_id]
    while stack:
        pid = stack.pop()
        for cid in _children_map.get(pid, []):
            result.append(cid)
            stack.append(cid)
    return result


def get_children(category_id: int, categories: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Возвращает список дочерних категорий (только первый уровень) с полями id, name."""
    cats = categories or load_categories()
    return [{"id": c["id"], "name": c["name"]} for c in cats if c.get("parent_id") == category_id]
