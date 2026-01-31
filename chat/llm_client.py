"""
Интерфейс LLM и реализации: локальный шаблон (без внешнего API) и заглушка внешнего LLM.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, List

from config import LLM_MODE

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Интерфейс клиента LLM для генерации ответа по контексту."""

    @abstractmethod
    def reply(self, user_message: str, products_context: str) -> str:
        """Возвращает текстовый ответ по запросу пользователя и контексту (список товаров)."""
        pass


class LocalTemplateLLM(LLMClient):
    """
    Без настоящего LLM: формирует ответ по шаблону на основе найденных товаров.
    Подходит для MVP и работы без облаков.
    """

    def reply(self, user_message: str, products_context: str) -> str:
        if not products_context or products_context.strip() == "Список товаров пуст.":
            return "По вашему запросу ничего не найдено. Попробуйте изменить формулировку или указать категорию и бюджет."
        return (
            "Вот подходящие варианты:\n\n" + products_context + "\n\nЕсли нужно сузить выбор — укажите бюджет или бренд."
        )


class ExternalLLM(LLMClient):
    """
    Внешний LLM по env (OpenAI/другое). Пока заглушка — возвращает шаблонный ответ.
    Позже можно подключить openai.Client или другой провайдер.
    """

    def __init__(self):
        logger.warning("ExternalLLM is stub; using template reply. Set OPENAI_API_KEY and implement request to use.")

    def reply(self, user_message: str, products_context: str) -> str:
        # Заглушка: тот же шаблон, что и LocalTemplateLLM
        client = LocalTemplateLLM()
        return client.reply(user_message, products_context)


def get_llm_client() -> LLMClient:
    """Возвращает клиент LLM в зависимости от AI_LLM_MODE."""
    if LLM_MODE == "external":
        return ExternalLLM()
    return LocalTemplateLLM()
