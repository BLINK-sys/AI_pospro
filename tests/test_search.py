"""
Минимальные тесты: фильтры и формат результатов поиска.
Запуск из корня AI_pospro: pip install -r requirements.txt && python -m pytest tests/test_search.py -v
"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import pytest

# apply_filters не требует faiss
from retrieval.filters import apply_filters


def test_apply_filters_price():
    meta = [
        {"product_id": 1, "price": 100, "quantity": 1},
        {"product_id": 2, "price": 200, "quantity": 0},
        {"product_id": 3, "price": 300, "quantity": 2},
    ]
    indices = [0, 1, 2]
    scores = [0.9, 0.8, 0.7]
    idx, sc = apply_filters(meta, indices, scores, price_min=150, price_max=250)
    assert idx == [1]
    assert len(sc) == 1


def test_apply_filters_in_stock():
    meta = [
        {"product_id": 1, "price": 100, "quantity": 1},
        {"product_id": 2, "price": 200, "quantity": 0},
    ]
    indices = [0, 1]
    scores = [0.9, 0.8]
    idx, sc = apply_filters(meta, indices, scores, in_stock_only=True)
    assert idx == [0]
    assert len(sc) == 1


def test_search_products_returns_list():
    """Без индекса search_products возвращает пустой список. Требует faiss/sentence_transformers."""
    try:
        from retrieval.search import search_products
    except ImportError:
        pytest.skip("faiss/sentence_transformers not installed")
    result = search_products("холодильник", top_k=5)
    assert isinstance(result, list)
    for item in result:
        assert "product_id" in item or "name" in item
        assert "score" in item
