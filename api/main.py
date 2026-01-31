"""
FastAPI-сервис AI: один эндпоинт чата.
Запуск из корня AI_pospro: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""
import sys
import threading
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import ChatRequest, ChatResponse, ProductOut
from chat.chat_engine import run_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_index_in_background() -> None:
    """Строит индекс в фоне (для Render: DATABASE_URL доступен только в runtime)."""
    try:
        from index.build_index import build
        build()
    except Exception as e:
        logger.exception("Background index build failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI_pospro service starting")
    from config import META_PATH, FAISS_INDEX_PATH, INDEX_DIR
    from index.faiss_store import VECTORS_NPY_PATH
    index_exists = META_PATH.exists() and (FAISS_INDEX_PATH.exists() or VECTORS_NPY_PATH.exists())
    if not index_exists:
        logger.info("Index not found, building in background (may take ~10 min)")
        t = threading.Thread(target=_build_index_in_background, daemon=True)
        t.start()
    yield
    logger.info("AI_pospro service shutting down")


app = FastAPI(
    title="AI Pospro",
    description="MVP: подбор товаров и чат",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Запрос к ИИ: подбор товаров по смыслу + фильтры.
    Возвращает текст ответа, список товаров (id, name, price, url, image_url, score) и опционально уточняющий вопрос.
    """
    result = run_chat(
        request.query,
        price_min=request.price_min,
        price_max=request.price_max,
        category_id=request.category_id,
        brand_id=request.brand_id,
        in_stock_only=request.in_stock_only,
    )
    return ChatResponse(
        message=result["message"],
        products=[ProductOut(**p) for p in result["products"]],
        clarifying_question=result.get("clarifying_question"),
    )
