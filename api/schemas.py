"""
Pydantic-схемы запроса и ответа для AI API.
"""
from typing import Any, List

from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: int | None = None
    name: str | None = None
    price: float | None = None
    url: str | None = None
    image_url: str | None = None
    score: float | None = None


class ChatRequest(BaseModel):
    """Запрос к чату: текст запроса и опциональные фильтры."""
    query: str = Field(..., min_length=1, description="Текст запроса пользователя")
    price_min: float | None = Field(None, description="Минимальная цена")
    price_max: float | None = Field(None, description="Максимальная цена")
    category_id: int | None = Field(None, description="ID категории")
    brand_id: int | None = Field(None, description="ID бренда")
    in_stock_only: bool = Field(False, description="Только товары в наличии")


class ChatResponse(BaseModel):
    """Ответ чата: текст, список товаров, уточняющий вопрос."""
    message: str = Field(..., description="Текстовый ответ")
    products: List[ProductOut] = Field(default_factory=list, description="Рекомендованные товары")
    clarifying_question: str | None = Field(None, description="Уточняющий вопрос при необходимости")
