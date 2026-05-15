"""
Агент Ануфрий с полным доступом к shell, файлам и браузеру.
"""

import json
import asyncio
import os
from typing import List, Dict, Any
from openai import AsyncOpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAX_ITERATIONS
from tools.shell import run_shell
from tools.filesystem import read_file, write_file, list_dir, search_files
from tools.browser import (
    browser_navigate, browser_click, browser_type, 
    browser_get_text, browser_screenshot, browser_close
)

client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

# Описания инструментов для LLM (OpenAI Functions format)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Выполняет shell-команду на локальной Linux-машине. Используй для: установки пакетов, запуска скриптов, работы с git, mongosh, docker и любых системных операций.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell-команда для выполнения"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Таймаут в секундах (по умолчанию 60)",
                        "default": 60
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает содержимое файла из рабочей директории.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Относительный путь к файлу"},
                    "offset": {"type": "integer", "description": "Номер начальной строки", "default": 0},
                    "limit": {"type": "integer", "description": "Макс. количество строк", "default": 100}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Создаёт или перезаписывает файл.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Относительный путь"},
                    "content": {"type": "string", "description": "Содержимое файла"},
                    "append": {"type": "boolean", "description": "Дописать в конец", "default": False}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Показывает содержимое директории.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Относительный путь", "default": "."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Открывает URL в headless-браузере (Chromium).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL для открытия"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_get_text",
            "description": "Получает текст со страницы браузера.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS-селектор", "default": "body"}
                },
                "required": []
            }
        }
    }
]

SYSTEM_PROMPT = """Ты — агент с полным доступом к локальной Linux-системе.
У тебя есть инструменты:
- run_shell — выполняет любые терминальные команды
- read_file / write_file / list_dir — работа с файлами
- browser_navigate / browser_get_text — управление браузером

Правила:
1. Всегда проверяй наличие инструментов перед использованием (which, command -v)
2. Для сложных задач разбивай на шаги
3. Читай вывод команд перед следующим шагом
4. Не выполняй rm -rf /, mkfs, dd на диски без подтверждения
5. Если задача требует установки — используй apt, pip, npm и т.д.

Рабочая директория: ~/agent-workspace
"""

async def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Выполняет вызванный инструмент."""
    if name == "run_shell":
        return run_shell(arguments["command"], arguments.get("timeout", 60))
    elif name == "read_file":
        return read_file(arguments["path"], arguments.get("offset", 0), arguments.get("limit", 100))
    elif name == "write_file":
        return write_file(arguments["path"], arguments["content"], arguments.get("append", False))
    elif name == "list_dir":
        return list_dir(arguments.get("path", "."))
    elif name == "browser_navigate":
        return await browser_navigate(arguments["url"])
    elif name == "browser_get_text":
        return await browser_get_text(arguments.get("selector", "body"))
    else:
        return {"error": f"Неизвестный инструмент: {name}"}

async def agent_loop(user_message: str) -> str:
    """
    Основной цикл агента:
    1. Отправляет сообщение LLM с доступными инструментами
    2. Получает ответ (текст или tool_call)
    3. Выполняет инструмент
    4. Отправляет результат обратно в LLM
    5. Повторяет до MAX_ITERATIONS или финального ответа
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    for iteration in range(MAX_ITERATIONS):
        print(f"\n--- Итерация {iteration + 1} ---")
        
        # Запрос к LLM
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.1
        )
        
        message = response.choices[0].message
        
        # Если LLM дал финальный ответ — возвращаем
        if not message.tool_calls:
            return message.content or "Готово."
        
        # Добавляем ответ ассистента (с tool_calls) в историю
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in message.tool_calls
            ]
        })
        
        # Выполняем все запрошенные инструменты
        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Вызов: {name}({json.dumps(args, ensure_ascii=False)})")
            
            result = await execute_tool(name, args)
            result_str = json.dumps(result, ensure_ascii=False, default=str)
            
            print(f"📤 Результат: {result_str[:500]}{'...' if len(result_str) > 500 else ''}")
            
            # Добавляем результат в историю
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str
            })
    
    return "Достигнут лимит итераций. Задача не завершена."

async def main():
    print("=" * 50)
    print("🤖 Агент с доступом к shell (Ctrl+C для выхода)")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n💬 Вы: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "выход"]:
                break
            
            print("\n⏳ Агент думает...")
            result = await agent_loop(user_input)
            print(f"\n🤖 Агент: {result}")
            
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

    await browser_close()

if __name__ == "__main__":
    asyncio.run(main())
