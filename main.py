"""
Агент Ануфрий с полным доступом к shell, файлам и браузеру.
"""

import json
import asyncio
import os
import uuid
from typing import List, Dict, Any
from openai import AsyncOpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAX_ITERATIONS
from tools.shell import run_shell
from tools.filesystem import read_file, write_file, list_dir, search_files
from tools.browser import (
    browser_navigate, browser_click, browser_type, 
    browser_get_text, browser_screenshot, browser_search_google, 
    browser_extract_content, browser_close
)
from tools.memory_tools import (
    memory_save_fact, memory_search, memory_get_summary, 
    memory_cleanup, get_memory_manager
)
from tools.task_tools import (
    task_create, task_add_attempt, task_add_insight,
    task_update_status, task_get_context, task_list_incomplete,
    task_search_similar
)
from tools.result_tools import (
    result_save, result_get, result_list, result_get_latest,
    result_delete, get_results_manager
)
from skills.loader import SkillLoader
from tools.skills_runner import run_skill_script

# Инициализация загрузчика навыков
skill_loader = SkillLoader()
skill_loader.scan()

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
    },
    {
        "type": "function",
        "function": {
            "name": "browser_search_google",
            "description": "Выполняет поиск в Google с антидетект мерами. Возвращает список результатов с заголовками, ссылками и описаниями. Используй вместо browser_navigate для поиска в Google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос для Google"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_extract_content",
            "description": "Извлекает текстовый контент со страницы по URL. ОБЯЗАТЕЛЬНО используй после browser_search_google для получения детальной информации со страниц из результатов поиска.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL страницы для извлечения контента"},
                    "selectors": {"type": "array", "items": {"type": "string"}, "description": "CSS селекторы для извлечения (опционально)", "default": None}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_save_fact",
            "description": "Сохраняет важный факт в долговременную память агента. Используй для: информации о пользователе, успешных решений, настроек, важных выводов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Содержимое факта для сохранения"},
                    "category": {"type": "string", "description": "Категория (user_info, solution, preference, skill, general)", "default": "general"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Ищет релевантную информацию в долговременной памяти агента. Используй когда нужно вспомнить что-то из прошлых диалогов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"},
                    "limit": {"type": "integer", "description": "Максимальное количество результатов", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_get_summary",
            "description": "Получает статистику по памяти агента (количество фактов, диалогов, навыков).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_cleanup",
            "description": "Очищает устаревшие данные из памяти (удаляет малозначимую информацию старше N дней).",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Удалить данные старше N дней", "default": 30}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_create",
            "description": "Создаёт новую задачу для отслеживания. Используй в начале сложной задачи, чтобы сохранить контекст.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Описание задачи"}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_add_attempt",
            "description": "Фиксирует попытку выполнения задачи с результатом. Используй после каждой попытки решения.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"},
                    "actions_taken": {"type": "array", "items": {"type": "string"}, "description": "Список выполненных действий"},
                    "result": {"type": "string", "description": "Результат попытки"},
                    "success": {"type": "boolean", "description": "Успешна ли попытка"},
                    "error_message": {"type": "string", "description": "Сообщение об ошибке (если есть)"}
                },
                "required": ["task_id", "actions_taken", "result", "success"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_add_insight",
            "description": "Добавляет ключевой вывод из задачи. Используй для сохранения важных находок.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"},
                    "content": {"type": "string", "description": "Содержание вывода"},
                    "insight_type": {"type": "string", "description": "Тип (learning, solution, blocker, workaround)", "default": "learning"}
                },
                "required": ["task_id", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_update_status",
            "description": "Обновляет статус задачи (in_progress, completed, failed, blocked).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"},
                    "status": {"type": "string", "description": "Новый статус"}
                },
                "required": ["task_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_get_context",
            "description": "Получает полный контекст задачи для продолжения работы. Используй когда пользователь просит повторить задачу.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_list_incomplete",
            "description": "Показывает список незавершённых задач текущей сессии.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_search_similar",
            "description": "Ищет похожие успешно выполненные задачи. Полезно для поиска решений.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Описание задачи для поиска"},
                    "limit": {"type": "integer", "description": "Максимальное количество результатов", "default": 5}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_save",
            "description": "КРИТИЧЕСКИ ВАЖНО: Сохраняет результат выполнения задачи для последующего использования. ВСЕГДА используй после получения важных данных (поиск, извлечение контента, списки компаний и т.д.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_type": {"type": "string", "description": "Тип результата (search_results, extracted_data, companies_list, contacts, etc.)"},
                    "content": {"type": "string", "description": "Содержимое результата в JSON формате"},
                    "title": {"type": "string", "description": "Заголовок результата (например, 'Список транспортных компаний')"},
                    "task_id": {"type": "integer", "description": "ID связанной задачи (опционально)"},
                    "ttl_hours": {"type": "integer", "description": "Время жизни результата в часах", "default": 24}
                },
                "required": ["result_type", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_get",
            "description": "Получает сохранённый результат по ID. Используй когда нужно получить данные из предыдущих операций.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_id": {"type": "integer", "description": "ID результата"}
                },
                "required": ["result_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_list",
            "description": "Показывает список сохранённых результатов текущей сессии. Используй чтобы увидеть доступные результаты.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_type": {"type": "string", "description": "Фильтр по типу результата (опционально)"},
                    "limit": {"type": "integer", "description": "Максимальное количество результатов", "default": 10}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_get_latest",
            "description": "Получает последний сохранённый результат из сессии. Полезно когда пользователь просит использовать 'последние данные'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_type": {"type": "string", "description": "Фильтр по типу результата (опционально)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skill_get_info",
            "description": "Получает полную информацию о навыке (инструкции, примеры использования). Используй когда пользователь упоминает триггеры навыка.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "Название навыка (например, 'mongo-compass')"}
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skill_run_script",
            "description": "Выполняет скрипт из навыка. Используй для специализированных операций (например, query_mongodb.sh для MongoDB).",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "Название навыка"},
                    "script_name": {"type": "string", "description": "Имя скрипта (например, 'query_mongodb.sh')"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Аргументы для скрипта", "default": []},
                    "timeout": {"type": "integer", "description": "Таймаут в секундах", "default": 60}
                },
                "required": ["skill_name", "script_name"]
            }
        }
    }
]

# Получаем каталог навыков для system prompt
SKILLS_CATALOG = skill_loader.get_catalog_prompt()

SYSTEM_PROMPT = f"""Ты — агент с полным доступом к локальной Linux-системе и долговременной памятью.

У тебя есть инструменты:
- run_shell — выполняет любые терминальные команды
- read_file / write_file / list_dir — работа с файлами
- browser_navigate / browser_get_text — управление браузером
- browser_search_google — поиск в Google с антидетект мерами
- browser_extract_content — извлекает контент со страниц (ОБЯЗАТЕЛЬНО используй после поиска!)
- memory_save_fact — сохраняет важную информацию в долговременную память
- memory_search — ищет релевантную информацию из прошлых диалогов
- memory_get_summary — показывает статистику памяти
- memory_cleanup — очищает устаревшие данные
- task_create — создаёт задачу для отслеживания (используй для сложных задач)
- task_add_attempt — фиксирует попытку выполнения с результатом
- task_add_insight — сохраняет ключевые выводы из задачи
- task_update_status — обновляет статус задачи (completed/failed/blocked)
- task_get_context — получает контекст задачи для продолжения
- task_list_incomplete — показывает незавершённые задачи
- task_search_similar — ищет похожие успешные решения
- result_save — сохраняет результат для последующего использования (ОБЯЗАТЕЛЬНО используй!)
- result_get — получает сохранённый результат по ID
- result_list — показывает список сохранённых результатов
- result_get_latest — получает последний сохранённый результат
- skill_get_info — получает полную информацию о навыке
- skill_run_script — выполняет специализированный скрипт из навыка

Правила работы с памятью:
- Автоматически сохраняй важную информацию: факты о пользователе, успешные решения, настройки
- Используй memory_search когда пользователь спрашивает о прошлых взаимодействиях
- Категории для фактов: user_info, solution, preference, skill, general

Правила работы с задачами:
- Для сложных задач создавай task_create в начале работы
- Фиксируй каждую попытку через task_add_attempt (действия, результат, успех/неудача)
- Сохраняй важные выводы через task_add_insight
- Обновляй статус задачи при завершении
- Если пользователь просит повторить — используй task_list_incomplete и task_get_context

КРИТИЧЕСКИ ВАЖНО - Правила работы с результатами:
- ВСЕГДА сохраняй результаты поиска и извлечения данных через result_save
- После browser_search_google → сохрани результаты через result_save
- После browser_extract_content → сохрани извлечённые данные через result_save
- После формирования списков (компании, контакты и т.д.) → сохрани через result_save
- Когда пользователь просит сохранить в файл — СНАЧАЛА проверь result_list или result_get_latest
- НЕ ПОВТОРЯЙ поиск если данные уже есть в сохранённых результатах!
- Пример правильной работы:
  1. Пользователь: "Найди компании грузоперевозчиков"
  2. Ты: browser_search_google → получаешь результаты
  3. Ты: result_save(result_type="search_results", content=результаты, title="Поиск грузоперевозчиков")
  4. Ты: browser_extract_content для каждого URL → получаешь данные
  5. Ты: result_save(result_type="companies_list", content=список_компаний, title="Список транспортных компаний")
  6. Пользователь: "Сохрани это в файл"
  7. Ты: result_get_latest(result_type="companies_list") → получаешь сохранённые данные
  8. Ты: write_file(path="companies.json", content=данные_из_результата)

Правила работы с поиском в интернете (КРИТИЧЕСКИ ВАЖНО!):
1. Для поиска информации ВСЕГДА используй browser_search_google (НЕ browser_navigate!)
2. После получения результатов поиска ОБЯЗАТЕЛЬНО используй browser_extract_content для каждого релевантного URL
3. Алгоритм работы с поиском:
   Шаг 1: browser_search_google("твой запрос") → получаешь список результатов с title, link, snippet
   Шаг 2: browser_extract_content(url) для 3-5 наиболее релевантных ссылок → получаешь полный контент
   Шаг 3: Анализируй полученный контент и формируй ответ пользователю
4. ПРИМЕР правильной работы:
   Задача: "Найди 5 компаний грузоперевозчиков"
   - Вызываешь: browser_search_google("компании грузоперевозчики Россия")
   - Получаешь 10 результатов с ссылками
   - Вызываешь: browser_extract_content(url1), browser_extract_content(url2), browser_extract_content(url3)...
   - Извлекаешь из контента названия компаний, контакты, услуги
   - Формируешь список из 5 компаний с деталями
5. НЕ ОСТАНАВЛИВАЙСЯ на результатах browser_search_google — они содержат только краткие описания!
6. Используй browser_extract_content чтобы получить ПОЛНУЮ информацию со страниц

Правила работы с навыками:
- Когда пользователь упоминает триггер навыка — используй skill_get_info для получения инструкций
- Следуй инструкциям из навыка для выполнения специализированных задач
- Используй skill_run_script для запуска скриптов навыка (например, query_mongodb.sh)
{SKILLS_CATALOG}

Общие правила:
1. Всегда проверяй наличие инструментов перед использованием (which, command -v)
2. Для сложных задач разбивай на шаги
3. Читай вывод команд перед следующим шагом
4. Не выполняй rm -rf /, mkfs, dd на диски без подтверждения
5. Если задача требует установки — используй apt, pip, npm и т.д.

Рабочая директория: ~/agent-workspace
"""

async def execute_tool(name: str, arguments: Dict[str, Any], session_id: str = "") -> Dict[str, Any]:
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
    elif name == "browser_search_google":
        return await browser_search_google(arguments["query"])
    elif name == "browser_extract_content":
        return await browser_extract_content(arguments["url"], arguments.get("selectors"))
    elif name == "memory_save_fact":
        return await memory_save_fact(arguments["content"], arguments.get("category", "general"))
    elif name == "memory_search":
        return await memory_search(arguments["query"], arguments.get("limit", 5))
    elif name == "memory_get_summary":
        return await memory_get_summary()
    elif name == "memory_cleanup":
        return await memory_cleanup(arguments.get("days", 30))
    elif name == "task_create":
        return task_create(session_id, arguments["description"], arguments.get("metadata"))
    elif name == "task_add_attempt":
        return task_add_attempt(
            arguments["task_id"],
            arguments["actions_taken"],
            arguments["result"],
            arguments["success"],
            arguments.get("error_message")
        )
    elif name == "task_add_insight":
        return task_add_insight(
            arguments["task_id"],
            arguments["content"],
            arguments.get("insight_type", "learning"),
            arguments.get("importance", 5)
        )
    elif name == "task_update_status":
        return task_update_status(arguments["task_id"], arguments["status"])
    elif name == "task_get_context":
        return task_get_context(arguments["task_id"])
    elif name == "task_list_incomplete":
        return task_list_incomplete(session_id)
    elif name == "task_search_similar":
        return task_search_similar(arguments["description"], arguments.get("limit", 5))
    elif name == "skill_get_info":
        skill = skill_loader.load_full(arguments["skill_name"])
        if skill:
            return {
                "success": True,
                "name": skill.name,
                "description": skill.description,
                "content": skill.content,
                "triggers": skill.triggers
            }
        else:
            return {"success": False, "error": f"Навык '{arguments['skill_name']}' не найден"}
    elif name == "skill_run_script":
        return run_skill_script(
            skill_loader,
            arguments["skill_name"],
            arguments["script_name"],
            arguments.get("args", []),
            arguments.get("timeout", 60)
        )
    elif name == "result_save":
        # Парсим content если это JSON строка
        content = arguments["content"]
        try:
            import json
            content = json.loads(content) if isinstance(content, str) else content
        except:
            pass
        
        return result_save(
            session_id=session_id,
            result_type=arguments["result_type"],
            content=content,
            title=arguments.get("title"),
            task_id=arguments.get("task_id"),
            ttl_hours=arguments.get("ttl_hours", 24)
        )
    elif name == "result_get":
        return result_get(arguments["result_id"])
    elif name == "result_list":
        return result_list(
            session_id=session_id,
            result_type=arguments.get("result_type"),
            limit=arguments.get("limit", 10)
        )
    elif name == "result_get_latest":
        return result_get_latest(
            session_id=session_id,
            result_type=arguments.get("result_type")
        )
    else:
        return {"error": f"Неизвестный инструмент: {name}"}

async def agent_loop(user_message: str, session_id: str) -> str:
    """
    Основной цикл агента:
    1. Отправляет сообщение LLM с доступными инструментами
    2. Получает ответ (текст или tool_call)
    3. Выполняет инструмент
    4. Отправляет результат обратно в LLM
    5. Повторяет до MAX_ITERATIONS или финального ответа
    """
    # Получаем менеджер памяти
    memory = get_memory_manager()
    
    # Сохраняем сообщение пользователя в память
    await memory.add_conversation(session_id, "user", user_message)
    
    # Получаем релевантный контекст из памяти
    memory_context = await memory.build_context_prompt(user_message, session_id)
    
    # Получаем контекст сохранённых результатов
    results_manager = get_results_manager()
    results_context = results_manager.build_results_context(session_id, limit=5)
    
    # Формируем system prompt с контекстом памяти и результатов
    system_prompt_with_memory = SYSTEM_PROMPT
    if memory_context:
        system_prompt_with_memory += f"\n\n{memory_context}"
    if results_context:
        system_prompt_with_memory += f"\n\n{results_context}"
    
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt_with_memory},
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
        
        # Если LLM дал финальный ответ — сохраняем и возвращаем
        if not message.tool_calls:
            final_response = message.content or "Готово."
            await memory.add_conversation(session_id, "assistant", final_response)
            return final_response
        
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
            
            result = await execute_tool(name, args, session_id)
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
    print("🤖 Агент Ануфрий с доступом к shell и памятью (Ctrl+C для выхода)")
    print("=" * 50)
    
    # Генерируем уникальный ID сессии
    session_id = str(uuid.uuid4())
    print(f"📝 ID сессии: {session_id[:8]}...")
    
    while True:
        try:
            user_input = input("\n💬 Вы: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "выход"]:
                break
            
            print("\n⏳ Агент думает...")
            result = await agent_loop(user_input, session_id)
            print(f"\n🤖 Агент: {result}")
            
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")

    await browser_close()

if __name__ == "__main__":
    asyncio.run(main())
