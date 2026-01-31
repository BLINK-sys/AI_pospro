# Разведка по проекту — товары и API

## Где хранятся товары
- **Таблица:** `product` (модель `pospro_new_server/models/product.py`, класс `Product`).
- **Связи:** `category` (category_id), `brand` (brand_id), `product_media`, `product_characteristic`; справочник названий характеристик — `characteristics_list` (ProductCharacteristic.key = id из списка).

## Поля товара (реально есть)
| Поле | Есть | Модель/API |
|------|------|------------|
| id | ✅ | Product.id |
| name / title | ✅ | Product.name |
| description | ✅ | Product.description (Text) |
| category / category_id | ✅ | Product.category_id, Product.category.name |
| brand | ✅ | Product.brand_id, Product.brand_info.name |
| price | ✅ | Product.price |
| quantity | ✅ | Product.quantity |
| image | ✅ | ProductMedia (первое по order), поле `image` в API |
| specs / characteristics | ✅ | ProductCharacteristic + CharacteristicsList (key → characteristic_key, value) |
| slug | ✅ | Product.slug (для URL) |
| is_visible, is_draft | ✅ | для фильтра видимых товаров |

## API товаров
- `GET /products/<slug>` — один товар с characteristics, media.
- `GET /products/bulk?ids=...` — список товаров (serialize_product).
- Список по категории — в `public_homepage` (get_category_with_children_and_products).

## Где интегрировать AI
- **Отдельный сервис** в `AI_pospro/` (FastAPI) — свой индекс FAISS, эмбеддинги, чат.
- Каталог для индекса загружать **напрямую из БД** (тот же PostgreSQL по DATABASE_URL).
