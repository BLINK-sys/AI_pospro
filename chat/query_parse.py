"""
Извлечение фильтров из текста запроса (бюджет: «до 500 тысяч», «бюджет 300 тыс» и т.п.).
"""
import re
from typing import Tuple


def parse_budget_from_query(query: str) -> Tuple[float | None, float | None]:
    """
    Парсит из текста запроса примерный бюджет (цена от/до).
    Возвращает (price_min, price_max) или (None, None).
    """
    if not query or not query.strip():
        return None, None
    text = query.strip().lower()
    price_min: float | None = None
    price_max: float | None = None

    # до N тысяч / до N тыс / до N 000 / до Nк
    m = re.search(
        r"до\s+(\d[\d\s]*)\s*(тысяч|тыс|к|000)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        n = int(re.sub(r"\s", "", m.group(1)))
        if n < 1000:
            price_max = n * 1000
        else:
            price_max = float(n)

    # до N млн / до N миллион
    m = re.search(r"до\s+(\d[\d\s]*)\s*(млн|миллион)\b", text, re.IGNORECASE)
    if m:
        n = float(re.sub(r"\s", "", m.group(1)).replace(",", "."))
        price_max = n * 1_000_000

    # бюджет N (если N < 10000 — считаем тысячами)
    m = re.search(r"бюджет\s+(\d[\d\s]*)", text, re.IGNORECASE)
    if m and price_max is None:
        n = int(re.sub(r"\s", "", m.group(1)))
        if n < 10000:
            price_max = n * 1000
        else:
            price_max = float(n)

    # от N тысяч
    m = re.search(r"от\s+(\d[\d\s]*)\s*(тысяч|тыс|к)\b", text, re.IGNORECASE)
    if m:
        n = int(re.sub(r"\s", "", m.group(1)))
        if n < 1000:
            price_min = n * 1000
        else:
            price_min = float(n)

    return price_min, price_max
