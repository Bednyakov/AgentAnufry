#!/usr/bin/env python3
"""
Тестовый скрипт для проверки кроссплатформенной работы shell.
Проверяет определение ОС и выполнение базовых команд.
"""

import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.shell import detect_os, get_shell_config, get_dangerous_commands, run_shell
from config import WORKSPACE_DIR

def test_os_detection():
    """Тест определения операционной системы."""
    print("=" * 60)
    print("ТЕСТ 1: Определение операционной системы")
    print("=" * 60)
    
    os_type = detect_os()
    print(f"✓ Обнаружена ОС: {os_type}")
    
    shell_exec, use_shell = get_shell_config()
    print(f"✓ Shell: {shell_exec}")
    print(f"✓ Use shell: {use_shell}")
    
    dangerous = get_dangerous_commands()
    print(f"✓ Опасных команд для {os_type}: {len(dangerous)}")
    print(f"  Примеры: {dangerous[:3]}")
    
    print(f"✓ Рабочая директория: {WORKSPACE_DIR}")
    print()

def test_basic_commands():
    """Тест выполнения базовых команд."""
    print("=" * 60)
    print("ТЕСТ 2: Выполнение базовых команд")
    print("=" * 60)
    
    os_type = detect_os()
    
    # Команды для разных ОС
    if os_type == "windows":
        commands = [
            ("echo Hello from Windows", "Вывод текста"),
            ("dir", "Список файлов"),
            ("ver", "Версия Windows"),
        ]
    else:  # Linux или macOS
        commands = [
            ("echo 'Hello from Unix'", "Вывод текста"),
            ("pwd", "Текущая директория"),
            ("uname -s", "Имя ОС"),
            ("whoami", "Текущий пользователь"),
        ]
    
    for cmd, description in commands:
        print(f"\n📝 {description}: {cmd}")
        result = run_shell(cmd, timeout=5)
        
        if result["success"]:
            print(f"✓ Успешно (код: {result['returncode']})")
            print(f"  ОС: {result.get('os', 'unknown')}")
            if result["stdout"]:
                print(f"  Вывод: {result['stdout'].strip()[:100]}")
        else:
            print(f"✗ Ошибка (код: {result['returncode']})")
            print(f"  Stderr: {result['stderr'][:100]}")
    
    print()

def test_dangerous_commands():
    """Тест блокировки опасных команд."""
    print("=" * 60)
    print("ТЕСТ 3: Блокировка опасных команд")
    print("=" * 60)
    
    os_type = detect_os()
    
    # Опасные команды для разных ОС
    if os_type == "windows":
        dangerous_cmds = [
            "format c:",
            "del /s /q c:\\",
        ]
    else:
        dangerous_cmds = [
            "rm -rf /",
            "mkfs.ext4 /dev/sda",
        ]
    
    for cmd in dangerous_cmds:
        print(f"\n🚫 Проверка блокировки: {cmd}")
        result = run_shell(cmd, timeout=1)
        
        if not result["success"] and "Заблокирована" in result["stderr"]:
            print(f"✓ Команда успешно заблокирована")
        else:
            print(f"✗ ВНИМАНИЕ: Команда не была заблокирована!")
    
    print()

def test_workspace_creation():
    """Тест создания рабочей директории."""
    print("=" * 60)
    print("ТЕСТ 4: Работа с рабочей директорией")
    print("=" * 60)
    
    print(f"📁 Рабочая директория: {WORKSPACE_DIR}")
    
    if os.path.exists(WORKSPACE_DIR):
        print(f"✓ Директория существует")
        
        # Проверяем возможность записи
        test_file = os.path.join(WORKSPACE_DIR, "test_cross_platform.txt")
        try:
            with open(test_file, "w") as f:
                f.write("Test from cross-platform script\n")
            print(f"✓ Запись в директорию работает")
            
            # Удаляем тестовый файл
            os.remove(test_file)
            print(f"✓ Удаление файлов работает")
        except Exception as e:
            print(f"✗ Ошибка при работе с файлами: {e}")
    else:
        print(f"✗ Директория не существует")
    
    print()

def main():
    """Запуск всех тестов."""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ КРОССПЛАТФОРМЕННОЙ ПОДДЕРЖКИ SHELL")
    print("=" * 60 + "\n")
    
    try:
        test_os_detection()
        test_basic_commands()
        test_dangerous_commands()
        test_workspace_creation()
        
        print("=" * 60)
        print("✓ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ВЫПОЛНЕНИИ ТЕСТОВ: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
