"""
Создание/обновление FAISS-индекса из каталога товаров.
Запуск: python -m index.build_index (из корня AI_pospro) или из корня репо: python -m AI_pospro.index.build_index
"""
import logging
import sys
from pathlib import Path

# Корень AI_pospro в PYTHONPATH
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import FAISS_INDEX_PATH, META_PATH
from data_access.catalog_loader import load_catalog, build_search_text
from index.faiss_store import add_vectors, save_index
from retrieval.embedder import Embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build() -> None:
    """Загружает каталог, строит эмбеддинги и сохраняет индекс + мета."""
    catalog = load_catalog()
    if not catalog:
        logger.warning("Catalog is empty, nothing to index")
        return

    texts = [build_search_text(item) for item in catalog]
    if not any(t.strip() for t in texts):
        logger.warning("All search texts are empty")
        return

    embedder = Embedder()
    vectors = embedder.embed(texts)
    meta = [
        {
            "product_id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "slug": item["slug"],
            "image_url": item["image_url"],
            "category_id": item["category_id"],
            "category_name": item["category_name"],
            "brand_id": item["brand_id"],
            "brand_name": item["brand_name"],
            "quantity": item["quantity"],
        }
        for item in catalog
    ]
    index = add_vectors(vectors, meta)
    save_index(index, meta)
    logger.info("Index built: %d products, path %s", len(meta), FAISS_INDEX_PATH)


if __name__ == "__main__":
    build()
