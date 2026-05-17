#!/usr/bin/env python3
"""
Тест для проверки исправления дублирования рабочих директорий.
"""

import os
import tempfile
import shutil
from pathlib import Path

# Временно переопределяем WORKSPACE_DIR для теста
test_workspace = tempfile.mkdtemp(prefix="test_agent_workspace_")
print(f"Создана тестовая директория: {test_workspace}")

# Патчим config
import sys
sys.path.insert(0, os.path.dirname(__file__))
import config
original_workspace = config.WORKSPACE_DIR
config.WORKSPACE_DIR = test_workspace

# Импортируем после патча
from tools.filesystem import write_file, read_file, list_dir, _normalize_path

def test_normalize_path():
    """Тест функции нормализации путей."""
    workspace_name = os.path.basename(test_workspace)
    
    print("\n=== Тест нормализации путей ===")
    
    test_cases = [
        (f"{workspace_name}/file.txt", "file.txt"),
        (f"{workspace_name}/subdir/file.txt", "subdir/file.txt"),
        ("file.txt", "file.txt"),
        ("subdir/file.txt", "subdir/file.txt"),
        (workspace_name, "."),
        (".", "."),
    ]
    
    for input_path, expected in test_cases:
        result = _normalize_path(input_path)
        status = "✓" if result == expected else "✗"
        print(f"{status} _normalize_path('{input_path}') = '{result}' (ожидалось: '{expected}')")
        if result != expected:
            return False
    
    return True

def test_write_and_read():
    """Тест записи и чтения файлов."""
    print("\n=== Тест записи и чтения файлов ===")
    
    workspace_name = os.path.basename(test_workspace)
    
    # Тест 1: Обычный путь
    result1 = write_file("test1.txt", "Содержимое файла 1")
    print(f"✓ Запись 'test1.txt': {result1['success']}")
    print(f"  Путь: {result1.get('path', 'N/A')}")
    
    # Тест 2: Путь с дублирующимся префиксом (проблемный случай)
    result2 = write_file(f"{workspace_name}/test2.txt", "Содержимое файла 2")
    print(f"✓ Запись '{workspace_name}/test2.txt': {result2['success']}")
    print(f"  Путь: {result2.get('path', 'N/A')}")
    
    # Тест 3: Путь с поддиректорией
    result3 = write_file("subdir/test3.txt", "Содержимое файла 3")
    print(f"✓ Запись 'subdir/test3.txt': {result3['success']}")
    print(f"  Путь: {result3.get('path', 'N/A')}")
    
    # Тест 4: Путь с дублирующимся префиксом и поддиректорией
    result4 = write_file(f"{workspace_name}/subdir/test4.txt", "Содержимое файла 4")
    print(f"✓ Запись '{workspace_name}/subdir/test4.txt': {result4['success']}")
    print(f"  Путь: {result4.get('path', 'N/A')}")
    
    # Проверяем, что файлы созданы в правильных местах
    print("\n=== Проверка структуры директорий ===")
    
    expected_files = [
        Path(test_workspace) / "test1.txt",
        Path(test_workspace) / "test2.txt",
        Path(test_workspace) / "subdir" / "test3.txt",
        Path(test_workspace) / "subdir" / "test4.txt",
    ]
    
    all_correct = True
    for expected_file in expected_files:
        exists = expected_file.exists()
        status = "✓" if exists else "✗"
        print(f"{status} Файл существует: {expected_file}")
        if not exists:
            all_correct = False
    
    # Проверяем, что НЕ создана вложенная директория
    nested_dir = Path(test_workspace) / workspace_name
    if nested_dir.exists():
        print(f"✗ ОШИБКА: Создана вложенная директория {nested_dir}")
        all_correct = False
    else:
        print(f"✓ Вложенная директория НЕ создана (правильно)")
    
    return all_correct

def test_list_dir():
    """Тест листинга директорий."""
    print("\n=== Тест листинга директорий ===")
    
    workspace_name = os.path.basename(test_workspace)
    
    # Тест 1: Листинг корневой директории
    result1 = list_dir(".")
    print(f"✓ Листинг '.': {result1['success']}, файлов: {len(result1.get('items', []))}")
    
    # Тест 2: Листинг с дублирующимся префиксом
    result2 = list_dir(workspace_name)
    print(f"✓ Листинг '{workspace_name}': {result2['success']}, файлов: {len(result2.get('items', []))}")
    
    return result1['success'] and result2['success']

def main():
    """Запуск всех тестов."""
    try:
        print("=" * 60)
        print("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ДУБЛИРОВАНИЯ РАБОЧИХ ДИРЕКТОРИЙ")
        print("=" * 60)
        
        test1 = test_normalize_path()
        test2 = test_write_and_read()
        test3 = test_list_dir()
        
        print("\n" + "=" * 60)
        if test1 and test2 and test3:
            print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        print("=" * 60)
        
    finally:
        # Очистка
        print(f"\nУдаление тестовой директории: {test_workspace}")
        shutil.rmtree(test_workspace, ignore_errors=True)
        config.WORKSPACE_DIR = original_workspace

if __name__ == "__main__":
    main()
