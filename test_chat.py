"""
Тестовый скрипт: отправить запрос на /chat и получить ответ.

Использование:
  1. Записать текст в query.txt и запустить:
     python test_chat.py

  2. Или передать запрос аргументом:
     python test_chat.py "нужен тихий холодильник"

Ответ выводится в консоль и сохраняется в response.txt
"""
import sys
from pathlib import Path

import requests

# Корень AI_pospro
ROOT = Path(__file__).resolve().parent
API_URL = "http://127.0.0.1:8000/chat"
QUERY_FILE = ROOT / "query.txt"
RESPONSE_FILE = ROOT / "response.txt"


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
    else:
        if not QUERY_FILE.exists():
            QUERY_FILE.write_text("холодильник для кофейни\n", encoding="utf-8")
            print(f"Создан {QUERY_FILE} — отредактируйте и запустите снова.")
            return
        query = QUERY_FILE.read_text(encoding="utf-8").strip()

    if not query:
        print("Запрос пустой. Напишите текст в query.txt или передайте аргументом.")
        return

    print("Запрос:", query[:80] + ("..." if len(query) > 80 else ""))
    print("Отправка на", API_URL, "...")

    try:
        r = requests.post(
            API_URL,
            json={"query": query},
            timeout=60,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.ConnectionError:
        print("Ошибка: не удалось подключиться к API. Запустите сервер: uvicorn api.main:app --port 8000")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print("Ошибка запроса:", e)
        if hasattr(e, "response") and e.response is not None:
            print("Ответ:", e.response.text[:500])
        sys.exit(1)

    message = data.get("message", "")
    products = data.get("products", [])
    clarifying = data.get("clarifying_question")

    # Вывод в консоль
    print("\n" + "=" * 60)
    print("ОТВЕТ:")
    print("=" * 60)
    print(message)
    if products:
        print("\n--- Товары (%d) ---" % len(products))
        for i, p in enumerate(products[:10], 1):
            print(f"  {i}. {p.get('name', '—')} | {p.get('price')} тг | {p.get('url', '')}")
        if len(products) > 10:
            print(f"  ... и ещё {len(products) - 10}")
    if clarifying:
        print("\nУточнение:", clarifying)
    print("=" * 60)

    # Сохранить в файл
    lines = [
        "Запрос: " + query,
        "",
        "Ответ:",
        message,
        "",
    ]
    if products:
        lines.append("Товары:")
        for i, p in enumerate(products, 1):
            lines.append(f"  {i}. {p.get('name')} | {p.get('price')} | {p.get('url')}")
        lines.append("")
    if clarifying:
        lines.append("Уточнение: " + clarifying)
    RESPONSE_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nОтвет сохранён в {RESPONSE_FILE}")


if __name__ == "__main__":
    main()
