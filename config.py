"""
Конфигурация AI_pospro из переменных окружения.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# База данных (та же, что у основного сервера)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pospro:yfcnhjqrf@localhost:5432/pospro_server_db")

# Модель эмбеддингов (мультиязычная)
EMBEDDING_MODEL = os.getenv("AI_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Пути для индекса FAISS и метаданных
INDEX_DIR = Path(os.getenv("AI_INDEX_DIR", "index_data"))
FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
META_PATH = INDEX_DIR / "meta.json"

# LLM: local = шаблон без внешнего API, external = внешний провайдер
LLM_MODE = os.getenv("AI_LLM_MODE", "local").lower()

# Внешний LLM (заглушка / будущее использование)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EXTERNAL_LLM_API_BASE = os.getenv("EXTERNAL_LLM_API_BASE", "")
EXTERNAL_LLM_MODEL = os.getenv("EXTERNAL_LLM_MODEL", "gpt-4")

# Поиск и ответ (50–70 товаров в ответе)
RETRIEVAL_TOP_K = int(os.getenv("AI_RETRIEVAL_TOP_K", "100"))
MAX_PRODUCTS_IN_RESPONSE = int(os.getenv("AI_MAX_PRODUCTS_IN_RESPONSE", "70"))

# URL фронта и бэкенда (для ссылок и картинок в ответе)
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://pospro-new-ui.onrender.com").rstrip("/")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "https://pospro-backend.onrender.com").rstrip("")
