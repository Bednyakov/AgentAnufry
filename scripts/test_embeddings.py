#!/usr/bin/env python3
"""
Тест для проверки работы embeddings и семантического поиска
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.manager import MemoryManager


async def test_embeddings():
    """Тестирует работу embeddings и семантического поиска."""
    print("🧪 Тестирование embeddings и семантического поиска\n")
    
    # Создаем менеджер памяти
    print("1️⃣ Инициализация MemoryManager...")
    memory = MemoryManager(db_path="memory/test_embeddings.db")
    print(f"   ✅ Провайдер: {memory.embeddings_provider}")
    print(f"   ✅ Модель: {memory.embeddings_model}")
    print(f"   ✅ URL: {memory.embeddings_client.base_url}\n")
    
    # Тестируем получение embedding
    print("2️⃣ Тестирование получения embedding...")
    test_text = "Это тестовый текст для проверки embeddings"
    embedding = await memory._get_embedding(test_text)
    
    if embedding:
        print(f"   ✅ Embedding получен успешно!")
        print(f"   📊 Размерность вектора: {len(embedding)}")
        print(f"   📊 Первые 5 значений: {embedding[:5]}\n")
    else:
        print(f"   ❌ Не удалось получить embedding!")
        print(f"   ⚠️  Проверьте конфигурацию EMBEDDINGS_* в .env файле\n")
        return False
    
    # Добавляем тестовые факты
    print("3️⃣ Добавление тестовых фактов в память...")
    facts = [
        ("Python - это высокоуровневый язык программирования", "programming"),
        ("JavaScript используется для веб-разработки", "programming"),
        ("Машинное обучение - это подраздел искусственного интеллекта", "ai"),
        ("Docker - это платформа для контейнеризации приложений", "devops"),
        ("Git - это система контроля версий", "devops"),
    ]
    
    for content, category in facts:
        fact_id = await memory.add_fact(content, category=category, importance=7)
        print(f"   ✅ Добавлен факт #{fact_id}: {content[:50]}...")
    
    print()
    
    # Тестируем семантический поиск
    print("4️⃣ Тестирование семантического поиска...\n")
    
    queries = [
        "Расскажи про языки программирования",
        "Что такое контейнеры?",
        "Искусственный интеллект и нейросети",
    ]
    
    for query in queries:
        print(f"   🔍 Запрос: '{query}'")
        results = await memory.search_facts(query, limit=2, min_importance=5)
        
        if results:
            print(f"   ✅ Найдено {len(results)} релевантных фактов:")
            for i, result in enumerate(results, 1):
                print(f"      {i}. [{result['category']}] {result['content']}")
                print(f"         Сходство: {result['similarity']:.3f}, Важность: {result['importance']}/10")
        else:
            print(f"   ❌ Факты не найдены (семантический поиск не работает)")
        print()
    
    # Статистика памяти
    print("5️⃣ Статистика памяти:")
    summary = await memory.get_memory_summary()
    print(f"   📊 Всего фактов: {summary['facts_count']}")
    print(f"   📊 Средняя важность: {summary['avg_importance']}")
    print(f"   📊 Категории: {summary['top_categories']}\n")
    
    print("✅ Тест завершен успешно!")
    print("\n💡 Если вы видите embeddings и результаты поиска - семантический поиск работает!")
    
    # Удаляем тестовую БД
    import os
    if os.path.exists("memory/test_embeddings.db"):
        os.remove("memory/test_embeddings.db")
        print("🧹 Тестовая база данных удалена")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_embeddings())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении теста: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
