#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы веб-поиска агента.
"""

import asyncio
from tools.browser import browser_search_google, browser_extract_content, browser_close

async def test_search_and_extract():
    """Тестирует поиск и извлечение контента."""
    
    print("=" * 60)
    print("🧪 ТЕСТ: Поиск и извлечение контента")
    print("=" * 60)
    
    # Тест 1: Поиск в Google
    print("\n📍 Шаг 1: Выполняем поиск в Google...")
    query = "Python programming language"
    search_results = await browser_search_google(query)
    
    if search_results.get("success"):
        print(f"✅ Поиск успешен! Найдено результатов: {search_results.get('count', 0)}")
        print(f"\nПервые 3 результата:")
        for i, result in enumerate(search_results.get("results", [])[:3], 1):
            print(f"\n{i}. {result.get('title', 'Без заголовка')}")
            print(f"   URL: {result.get('link', 'N/A')}")
            print(f"   Описание: {result.get('snippet', 'N/A')[:100]}...")
    else:
        print(f"❌ Ошибка поиска: {search_results.get('error', 'Неизвестная ошибка')}")
        await browser_close()
        return
    
    # Тест 2: Извлечение контента с первой страницы
    if search_results.get("results"):
        first_url = search_results["results"][0].get("link")
        
        print(f"\n📍 Шаг 2: Извлекаем контент с первой страницы...")
        print(f"URL: {first_url}")
        
        content_result = await browser_extract_content(first_url)
        
        if content_result.get("success"):
            print(f"✅ Контент успешно извлечен!")
            print(f"   Заголовок: {content_result.get('title', 'N/A')}")
            print(f"   Размер контента: {content_result.get('content_length', 0)} символов")
            print(f"\nПервые 300 символов контента:")
            print("-" * 60)
            print(content_result.get('content', '')[:300] + "...")
            print("-" * 60)
        else:
            print(f"❌ Ошибка извлечения: {content_result.get('error', 'Неизвестная ошибка')}")
    
    # Закрываем браузер
    print("\n📍 Шаг 3: Закрываем браузер...")
    await browser_close()
    print("✅ Браузер закрыт")
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 60)

async def test_multiple_extractions():
    """Тестирует извлечение контента с нескольких страниц."""
    
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ: Извлечение контента с нескольких страниц")
    print("=" * 60)
    
    # Поиск
    print("\n📍 Выполняем поиск...")
    query = "грузоперевозки компании Россия"
    search_results = await browser_search_google(query)
    
    if not search_results.get("success"):
        print(f"❌ Ошибка поиска: {search_results.get('error')}")
        await browser_close()
        return
    
    print(f"✅ Найдено результатов: {search_results.get('count', 0)}")
    
    # Извлекаем контент с первых 3 страниц
    results = search_results.get("results", [])[:3]
    
    print(f"\n📍 Извлекаем контент с {len(results)} страниц...")
    
    for i, result in enumerate(results, 1):
        url = result.get("link")
        title = result.get("title", "Без заголовка")
        
        print(f"\n{i}. {title}")
        print(f"   URL: {url}")
        
        content = await browser_extract_content(url)
        
        if content.get("success"):
            print(f"   ✅ Контент извлечен ({content.get('content_length', 0)} символов)")
        else:
            print(f"   ❌ Ошибка: {content.get('error', 'N/A')}")
    
    await browser_close()
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТ ЗАВЕРШЕН!")
    print("=" * 60)

async def main():
    """Запускает все тесты."""
    try:
        # Тест 1: Базовый поиск и извлечение
        await test_search_and_extract()
        
        # Небольшая пауза между тестами
        await asyncio.sleep(2)
        
        # Тест 2: Множественное извлечение
        await test_multiple_extractions()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
        await browser_close()
    except Exception as e:
        print(f"\n\n❌ Ошибка во время теста: {e}")
        import traceback
        traceback.print_exc()
        await browser_close()

if __name__ == "__main__":
    print("\n🚀 Запуск тестов веб-поиска...")
    print("⏳ Это может занять некоторое время...\n")
    asyncio.run(main())
