#!/usr/bin/env python3
"""
Тест системы сохранения результатов.
Проверяет, что результаты сохраняются и извлекаются корректно.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.result_tools import (
    result_save, result_get, result_list, result_get_latest, result_delete
)
import uuid
import json


def test_results_system():
    """Тестирует систему сохранения результатов."""
    
    print("=" * 60)
    print("🧪 Тест системы сохранения результатов")
    print("=" * 60)
    
    # Генерируем уникальный session_id для теста
    session_id = str(uuid.uuid4())
    print(f"\n📝 Тестовая сессия: {session_id[:8]}...")
    
    # Тест 1: Сохранение результата
    print("\n--- Тест 1: Сохранение результата ---")
    test_data = {
        "companies": [
            {"name": "ТК Деловые Линии", "phone": "+7 (800) 250-00-00"},
            {"name": "ПЭК", "phone": "+7 (800) 234-34-34"},
            {"name": "СДЭК", "phone": "+7 (800) 250-25-25"}
        ]
    }
    
    result = result_save(
        session_id=session_id,
        result_type="companies_list",
        content=test_data,
        title="Тестовый список компаний",
        ttl_hours=1
    )
    
    if result["success"]:
        print(f"✅ Результат сохранён с ID: {result['result_id']}")
        saved_id = result["result_id"]
    else:
        print(f"❌ Ошибка сохранения: {result.get('error')}")
        return False
    
    # Тест 2: Получение результата по ID
    print("\n--- Тест 2: Получение результата по ID ---")
    result = result_get(saved_id)
    
    if result["success"]:
        print(f"✅ Результат получен:")
        print(f"   Тип: {result['result']['result_type']}")
        print(f"   Заголовок: {result['result']['title']}")
        print(f"   Компаний: {len(result['result']['content']['companies'])}")
    else:
        print(f"❌ Ошибка получения: {result.get('error')}")
        return False
    
    # Тест 3: Сохранение второго результата
    print("\n--- Тест 3: Сохранение второго результата ---")
    search_results = {
        "query": "транспортные компании",
        "results": [
            {"title": "Результат 1", "url": "https://example.com/1"},
            {"title": "Результат 2", "url": "https://example.com/2"}
        ]
    }
    
    result = result_save(
        session_id=session_id,
        result_type="search_results",
        content=search_results,
        title="Результаты поиска транспортных компаний"
    )
    
    if result["success"]:
        print(f"✅ Второй результат сохранён с ID: {result['result_id']}")
    else:
        print(f"❌ Ошибка сохранения: {result.get('error')}")
        return False
    
    # Тест 4: Список результатов
    print("\n--- Тест 4: Список результатов сессии ---")
    result = result_list(session_id=session_id, limit=10)
    
    if result["success"]:
        print(f"✅ Найдено результатов: {result['count']}")
        for r in result["results"]:
            print(f"   - ID {r['id']}: {r['title']} ({r['type']})")
    else:
        print(f"❌ Ошибка получения списка: {result.get('error')}")
        return False
    
    # Тест 5: Получение последнего результата
    print("\n--- Тест 5: Получение последнего результата ---")
    result = result_get_latest(session_id=session_id, result_type="companies_list")
    
    if result["success"]:
        print(f"✅ Последний результат типа 'companies_list':")
        print(f"   ID: {result['result']['id']}")
        print(f"   Заголовок: {result['result']['title']}")
    else:
        print(f"❌ Ошибка: {result.get('error')}")
        return False
    
    # Тест 6: Фильтрация по типу
    print("\n--- Тест 6: Фильтрация по типу результата ---")
    result = result_list(session_id=session_id, result_type="search_results")
    
    if result["success"]:
        print(f"✅ Найдено результатов типа 'search_results': {result['count']}")
        for r in result["results"]:
            print(f"   - {r['title']}")
    else:
        print(f"❌ Ошибка: {result.get('error')}")
        return False
    
    # Тест 7: Удаление результата
    print("\n--- Тест 7: Удаление результата ---")
    result = result_delete(saved_id)
    
    if result["success"]:
        print(f"✅ Результат #{saved_id} удалён")
    else:
        print(f"❌ Ошибка удаления: {result.get('error')}")
        return False
    
    # Проверка, что результат действительно удалён
    result = result_get(saved_id)
    if not result["success"]:
        print(f"✅ Подтверждено: результат больше не доступен")
    else:
        print(f"❌ Ошибка: результат всё ещё доступен")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Все тесты пройдены успешно!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_results_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
