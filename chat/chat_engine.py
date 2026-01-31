"""
Движок чата: поиск товаров, формирование контекста, ответ LLM, структура результата.
"""
import logging
import re
from typing import Any, List

from config import MAX_PRODUCTS_IN_RESPONSE, RETRIEVAL_TOP_K
from chat.prompts import (
    format_products_context,
    clarifying_question_no_results,
    clarifying_question_few_results,
    clarifying_question_subcategory,
)
from chat.llm_client import get_llm_client
from chat.query_parse import parse_budget_from_query
from data_access.categories_loader import get_descendant_ids
from retrieval.search import search_products
from retrieval.rerank import rerank
from retrieval.category_match import match_query_to_category

logger = logging.getLogger(__name__)


def _query_mentions_any(query: str, names: list[str]) -> bool:
    """Проверяет, есть ли в запросе упоминание любого из названий (или значимой части)."""
    q = (query or "").lower()
    for n in names:
        words = [w for w in re.split(r"\W+", (n or "").lower()) if len(w) >= 4]
        for w in words:
            if w in q:
                return True
    return False


def run_chat(
    query: str,
    *,
    price_min: float | None = None,
    price_max: float | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    in_stock_only: bool = False,
) -> dict[str, Any]:
    """
    Выполняет поиск по запросу, генерирует ответ и возвращает структуру:
    - message: текст ответа
    - products: список { id, name, price, url, image_url, score }
    - clarifying_question: уточняющий вопрос или None
    """
    # Извлекаем бюджет из текста («до 500 тысяч» → price_max=500000), если не передан явно
    parsed_min, parsed_max = parse_budget_from_query(query)
    effective_price_min = price_min if price_min is not None else parsed_min
    effective_price_max = price_max if price_max is not None else parsed_max
    if effective_price_max is not None:
        logger.info("Budget from query: price_max=%s", effective_price_max)
    if effective_price_min is not None:
        logger.info("Budget from query: price_min=%s", effective_price_min)

    # Определяем категорию по запросу (холодильник → Холодильное оборудование и подкатегории)
    category_ids: list[int] | None = None
    matched_category_name: str | None = None
    subcategory_children: list[dict] = []
    if category_id is None:
        cat_id, cat_name, children = match_query_to_category(query)
        if cat_id is not None:
            category_ids = get_descendant_ids(cat_id)
            matched_category_name = cat_name
            subcategory_children = children
            logger.info("Matched category: %s (id=%s), %d descendants", cat_name, cat_id, len(category_ids))

    search_fallback_used = False
    products = search_products(
        query,
        top_k=RETRIEVAL_TOP_K,
        price_min=effective_price_min,
        price_max=effective_price_max,
        category_id=category_id,
        category_ids=category_ids,
        brand_id=brand_id,
        in_stock_only=in_stock_only,
    )
    # Если с фильтром по категории ничего не нашли — повторяем поиск без категории (только бюджет и смысл)
    if not products and category_ids:
        logger.info("No results with category filter, retrying without category")
        search_fallback_used = True
        products = search_products(
            query,
            top_k=RETRIEVAL_TOP_K,
            price_min=effective_price_min,
            price_max=effective_price_max,
            category_id=None,
            category_ids=None,
            brand_id=brand_id,
            in_stock_only=in_stock_only,
        )
    products = rerank(query, products, top_k=MAX_PRODUCTS_IN_RESPONSE)

    # Нормализуем поля для ответа API
    products_out: List[dict[str, Any]] = []
    for p in products:
        products_out.append({
            "id": p.get("product_id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "url": p.get("url"),
            "image_url": p.get("image_url"),
            "score": p.get("score"),
        })

    context = format_products_context(products_out)
    llm = get_llm_client()
    message = llm.reply(query, context)
    if search_fallback_used and products_out:
        message += "\n\nПоказаны товары по бюджету и смыслу запроса. Для точного подбора укажите категорию (например: витрина холодильная, шкаф холодильный)."

    clarifying = None
    if not products_out:
        clarifying = clarifying_question_no_results()
    elif len(products_out) < 3:
        clarifying = clarifying_question_few_results()
    elif matched_category_name and len(subcategory_children) >= 3 and not _query_mentions_any(query, [c.get("name", "") for c in subcategory_children]):
        clarifying = clarifying_question_subcategory(
            matched_category_name,
            [c.get("name", "") for c in subcategory_children if c.get("name")],
        )

    return {
        "message": message,
        "products": products_out,
        "clarifying_question": clarifying,
    }
