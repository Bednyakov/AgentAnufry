"""
Тестирование классификатора важности информации.
Проверяет, почему LLM возвращает пустой ответ при классификации.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.manager import MemoryManager
from config import IMPORTANCE_CLASSIFIER_MODEL, LLM_MODEL, LLM_BASE_URL, LLM_PROVIDER


async def test_importance_classifier():
    print("🧪 Тестирование классификатора важности\n")
    
    print("1️⃣ Конфигурация:")
    print(f"   📌 Провайдер: {LLM_PROVIDER}")
    print(f"   📌 Модель классификатора: {IMPORTANCE_CLASSIFIER_MODEL}")
    print(f"   📌 Основная модель: {LLM_MODEL}")
    print(f"   📌 URL: {LLM_BASE_URL}\n")
    
    # Инициализируем менеджер памяти
    memory = MemoryManager(db_path="memory/test_classifier.db")
    
    # Тестовые примеры разной важности
    test_cases = [
        {
            "content": "Привет! Как дела?",
            "context": "Приветствие",
            "expected_range": (1, 3),
            "description": "Малозначимое приветствие"
        },
        {
            "content": "Пользователь предпочитает Python для разработки",
            "context": "Предпочтения пользователя",
            "expected_range": (4, 6),
            "description": "Средняя важность - предпочтения"
        },
        {
            "content": "Критическая ошибка: система не может подключиться к базе данных",
            "context": "Системная ошибка",
            "expected_range": (7, 10),
            "description": "Высокая важность - критическая ошибка"
        },
        {
            "content": "Успешно решена задача по оптимизации алгоритма поиска",
            "context": "Успешное решение",
            "expected_range": (7, 10),
            "description": "Высокая важность - успешное решение"
        }
    ]
    
    print("2️⃣ Тестирование классификации:\n")
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"   Тест {i}: {test['description']}")
        print(f"   📝 Контент: {test['content'][:60]}...")
        print(f"   🎯 Ожидаемый диапазон: {test['expected_range'][0]}-{test['expected_range'][1]}")
        
        try:
            importance = await memory.classify_importance(test['content'], test['context'])
            
            in_range = test['expected_range'][0] <= importance <= test['expected_range'][1]
            status = "✅" if in_range else "⚠️"
            
            print(f"   {status} Результат: {importance}/10")
            
            results.append({
                "test": test['description'],
                "importance": importance,
                "expected": test['expected_range'],
                "success": in_range
            })
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results.append({
                "test": test['description'],
                "importance": None,
                "expected": test['expected_range'],
                "success": False,
                "error": str(e)
            })
        
        print()
    
    print("3️⃣ Итоги тестирования:\n")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"   ✅ Успешных тестов: {successful}/{total}")
    
    if successful < total:
        print(f"   ⚠️ Неудачных тестов: {total - successful}/{total}")
        print("\n   Детали неудачных тестов:")
        for r in results:
            if not r['success']:
                print(f"   - {r['test']}: получено {r.get('importance', 'N/A')}, ожидалось {r['expected']}")
                if 'error' in r:
                    print(f"     Ошибка: {r['error']}")
    
    # Удаляем тестовую БД
    import os
    if os.path.exists("memory/test_classifier.db"):
        os.remove("memory/test_classifier.db")
        print("\n🧹 Тестовая база данных удалена")
    
    print("\n" + "="*60)
    if successful == total:
        print("✅ Все тесты пройдены успешно!")
        print("💡 Классификатор важности работает корректно")
    else:
        print("⚠️ Некоторые тесты не прошли")
        print("💡 Возможные причины:")
        print("   1. Модель не поддерживает короткие ответы (max_tokens=10)")
        print("   2. Модель возвращает пустой content (None)")
        print("   3. Модель не следует инструкциям промпта")
        print("   4. Проблемы с API или таймаутом")


if __name__ == "__main__":
    asyncio.run(test_importance_classifier())
