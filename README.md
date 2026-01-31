# AI_pospro — MVP «ИИ для магазина»

Подбор товаров по смыслу (RAG: эмбеддинги + FAISS + опционально LLM) и простой чат-ответ.

## Требования

- Python 3.10+
- Доступ к той же PostgreSQL, что и у основного сервера (переменная `DATABASE_URL`)

## Установка

```bash
cd AI_pospro
pip install -r requirements.txt
```

## Конфигурация (env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL PostgreSQL (как у основного сервера) | `postgresql://pospro:...@localhost:5432/pospro_server_db` |
| `AI_EMBEDDING_MODEL` | Модель sentence-transformers (мультиязычная) | `paraphrase-multilingual-MiniLM-L12-v2` |
| `AI_INDEX_DIR` | Папка для индекса FAISS и метаданных | `index_data` |
| `AI_LLM_MODE` | `local` — шаблонный ответ, `external` — внешний LLM (пока заглушка) | `local` |
| `AI_RETRIEVAL_TOP_K` | Сколько кандидатов забирать из поиска | `10` |
| `AI_MAX_PRODUCTS_IN_RESPONSE` | Сколько товаров возвращать в ответе | `8` |
| `FRONTEND_BASE_URL` | Базовый URL фронта (для ссылок на товары) | `https://pospro-new-ui.onrender.com` |
| `BACKEND_BASE_URL` | Базовый URL бэкенда (для картинок) | `https://pospro-backend.onrender.com` |

## Построение индекса

Перед первым запросом нужно собрать индекс по каталогу из БД:

```bash
cd AI_pospro
python -m index.build_index
```

Индекс сохраняется в `index_data/faiss.index` и `index_data/meta.json`. При изменении каталога запустите команду снова.

## Запуск API

```bash
cd AI_pospro
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- Чат: `POST http://localhost:8000/chat` с телом JSON (см. ниже).

## Примеры запросов

**POST /chat**

```json
{
  "query": "нужен холодильник для кофейни до 500 тыс, тихий, 2 двери",
  "price_max": 500000,
  "in_stock_only": false
}
```

Ответ:

```json
{
  "message": "Вот подходящие варианты:\n\n1. Холодильник ... — цена 450 000 тг. Ссылка: ...",
  "products": [
    {
      "id": 123,
      "name": "Холодильник ...",
      "price": 450000,
      "url": "https://pospro-new-ui.onrender.com/product/...",
      "image_url": "https://pospro-backend.onrender.com/uploads/...",
      "score": 0.82
    }
  ],
  "clarifying_question": null
}
```

При малом количестве или отсутствии результатов в `clarifying_question` вернётся уточняющий вопрос.

## Структура проекта

```
AI_pospro/
  README.md
  requirements.txt
  config.py
  RECON_SUMMARY.md
  data_access/
    catalog_loader.py   # загрузка товаров из БД
  index/
    build_index.py      # создание/обновление индекса
    faiss_store.py      # save/load FAISS + мета
  retrieval/
    embedder.py         # SentenceTransformer, нормализация
    search.py           # topK + фильтры (цена, категория, бренд, наличие)
    rerank.py           # заглушка переранжирования
  chat/
    prompts.py         # системные инструкции (RU)
    llm_client.py       # интерфейс LLM + LocalTemplateLLM, ExternalLLM (заглушка)
    chat_engine.py      # контекст → ответ → структура результата
  api/
    main.py             # FastAPI
    schemas.py          # Pydantic запрос/ответ
  tests/
    test_search.py      # тесты фильтров и формата результатов
```

## Тесты

```bash
cd AI_pospro
python -m pytest tests/ -v
```

## Деплой на Render

1. В [Render](https://render.com) нажмите **New → Web Service**.
2. Подключите репозиторий **BLINK-sys/AI_pospro** (или свой fork).
3. Render подхватит `render.yaml` (build без БД, start — uvicorn).
4. **Обязательно** в настройках сервиса добавьте переменную **DATABASE_URL** — connection string той же PostgreSQL, что у pospro-backend (в Render Dashboard → Environment).
5. Сохраните и запустите деплой. Билд установит зависимости (~5 мин). После старта сервис в фоне построит индекс по каталогу из БД (~10 мин) — пока индекс не готов, `/chat` вернёт пустой список; затем поиск заработает.
6. Проверка: `GET https://<ваш-сервис>.onrender.com/health`, затем `POST .../chat` с `{"query": "..."}`.

При обновлении каталога в БД сделайте **Redeploy** сервиса ai-pospro — при следующем старте индекс пересоберётся в фоне.
