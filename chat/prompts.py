"""
Системные инструкции и шаблоны для ответов чата (русский язык).
"""

SYSTEM_INSTRUCTION = """Ты — помощник по подбору товаров в магазине. Отвечай кратко и по делу на русском.
Используй только переданный список товаров. Если товаров мало или нет — предложи уточнить запрос (бюджет, категория, бренд)."""


def format_products_context(products: list[dict]) -> str:
    """Форматирует список товаров для вставки в контекст LLM или шаблон."""
    if not products:
        return "Список товаров пуст."
    lines = []
    for i, p in enumerate(products, 1):
        name = p.get("name", "")
        price = p.get("price")
        price_str = f"{price:,.0f}" if price is not None else "—"
        url = p.get("url", "")
        lines.append(f"{i}. {name} — цена {price_str} тг. Ссылка: {url}")
    return "\n".join(lines)


def clarifying_question_no_results() -> str:
    return "Уточните, пожалуйста: категория товара, бюджет или бренд?"


def clarifying_question_few_results() -> str:
    return "Найдено немного вариантов. Можете уточнить бюджет или требования?"


def clarifying_question_subcategory(category_name: str, child_names: list[str], max_show: int = 7) -> str:
    """Уточнение по подкатегории: «В категории X есть: A, B, C... Что именно вас интересует?»"""
    if not child_names:
        return ""
    show = child_names[:max_show]
    parts = ", ".join(show)
    if len(child_names) > max_show:
        parts += " и др."
    return f"В категории «{category_name}» есть: {parts}. Что именно вас интересует?"
