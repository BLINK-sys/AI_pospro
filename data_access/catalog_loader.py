"""
Загрузка каталога товаров из БД основного сервера (PostgreSQL).
Используется для построения индекса — прямой доступ к БД без Flask.
"""
import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DATABASE_URL

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """Создаёт движок SQLAlchemy для подключения к БД."""
    return create_engine(DATABASE_URL, pool_pre_ping=True)


def load_catalog(engine: Engine | None = None) -> list[dict[str, Any]]:
    """
    Загружает все видимые товары с полями для индексации.
    Возвращает список словарей: id, name, description, category_id, category_name,
    brand_id, brand_name, price, quantity, slug, image_url, specs_text.
    """
    eng = engine or get_engine()

    # Товары: видимые, не черновик
    products_sql = text("""
        SELECT p.id, p.name, p.description, p.price, p.quantity, p.slug,
               p.category_id, p.brand_id,
               c.name AS category_name,
               b.name AS brand_name
        FROM product p
        LEFT JOIN category c ON p.category_id = c.id
        LEFT JOIN brand b ON p.brand_id = b.id
        WHERE p.is_visible = true AND (p.is_draft = false OR p.is_draft IS NULL)
        ORDER BY p.id
    """)

    with eng.connect() as conn:
        rows = conn.execute(products_sql).fetchall()

    product_ids = [r.id for r in rows]
    if not product_ids:
        logger.warning("No visible products found in catalog")
        return []

    # Первое изображение по product_id
    ids_placeholders = ",".join(str(i) for i in product_ids)
    media_sql = text(f"""
        SELECT DISTINCT ON (product_id) product_id, url
        FROM product_media
        WHERE product_id IN ({ids_placeholders}) AND media_type = 'image'
        ORDER BY product_id, "order" NULLS LAST
    """)

    with eng.connect() as conn:
        media_rows = conn.execute(media_sql).fetchall()

    image_by_id = {r.product_id: r.url for r in media_rows}

    # Характеристики: key из справочника + value, сгруппировать по product_id
    chars_sql = text(f"""
        SELECT pc.product_id, cl.characteristic_key, pc.value
        FROM product_characteristic pc
        LEFT JOIN characteristics_list cl ON cl.id::text = pc.key
        WHERE pc.product_id IN ({ids_placeholders})
        ORDER BY pc.product_id, pc.sort_order NULLS LAST
    """)

    with eng.connect() as conn:
        char_rows = conn.execute(chars_sql).fetchall()

    specs_by_id: dict[int, list[str]] = {}
    for r in char_rows:
        specs_by_id.setdefault(r.product_id, []).append(f"{r.characteristic_key}: {r.value}")
    for pid in product_ids:
        if pid not in specs_by_id:
            specs_by_id[pid] = []

    # Собираем каталог
    catalog = []
    for r in rows:
        specs_text = " ".join(specs_by_id.get(r.id, []))
        catalog.append({
            "id": r.id,
            "name": r.name or "",
            "description": (r.description or "").strip(),
            "category_id": r.category_id,
            "category_name": r.category_name or "",
            "brand_id": r.brand_id,
            "brand_name": r.brand_name or "",
            "price": float(r.price or 0),
            "quantity": int(r.quantity or 0),
            "slug": r.slug or "",
            "image_url": image_by_id.get(r.id) or "",
            "specs_text": specs_text,
        })
    logger.info("Loaded %d products from catalog", len(catalog))
    return catalog


def build_search_text(item: dict[str, Any]) -> str:
    """
    Собирает один текст для эмбеддинга из полей товара (название, описание, характеристики).
    """
    parts = [
        item.get("name") or "",
        item.get("description") or "",
        item.get("category_name") or "",
        item.get("brand_name") or "",
        item.get("specs_text") or "",
    ]
    return " ".join(p for p in parts if p).strip()
