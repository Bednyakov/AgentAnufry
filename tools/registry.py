"""
Tool registry with lazy loading and consolidated tools.

Core tools are always available. Extended tools are loaded on demand
via tool_get_available / tool_use, reducing token usage by ~60-70%.
"""

from typing import Dict, List, Any, Optional

# Registry version for tracking changes and migrations
REGISTRY_VERSION = "1.0.0"

# === CORE TOOLS (always sent to LLM) ===
CORE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Выполняет shell-команду. Автоматически определяет ОС.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell-команда"},
                    "timeout": {"type": "integer", "description": "Таймаут в секундах", "default": 60}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает содержимое файла.",
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
            "name": "tool_get_available",
            "description": "Показывает доступные инструменты по категории. Вызывай чтобы узнать какие инструменты есть.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Категория: browser, memory, task, result, skill"
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_use",
            "description": "Вызывает инструмент из указанной категории. Сначала вызови tool_get_available чтобы узнать доступные действия.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Категория инструмента"},
                    "action": {"type": "string", "description": "Действие (см. tool_get_available)"},
                    "params": {"type": "object", "description": "Параметры действия"}
                },
                "required": ["category", "action"]
            }
        }
    },
]

# === EXTENDED TOOLS (loaded on demand) ===
EXTENDED_TOOLS: Dict[str, Dict[str, Any]] = {
    "browser": {
        "description": "Инструменты браузера: навигация, поиск Google, извлечение контента",
        "actions": {
            "navigate": {
                "description": "Открывает URL в headless-браузере",
                "params": {"url": {"type": "string", "description": "URL"}},
                "required": ["url"]
            },
            "get_text": {
                "description": "Получает текст со страницы",
                "params": {"selector": {"type": "string", "description": "CSS-селектор", "default": "body"}}
            },
            "search_google": {
                "description": "Поиск в Google с антидетект мерами. Возвращает список результатов.",
                "params": {"query": {"type": "string", "description": "Поисковый запрос"}},
                "required": ["query"]
            },
            "extract_content": {
                "description": "Извлекает контент со страницы по URL. ОБЯЗАТЕЛЬНО после browser/search_google!",
                "params": {"url": {"type": "string", "description": "URL страницы"}},
                "required": ["url"]
            },
            "navigate_search_page": {
                "description": "Навигация по страницам поисковой выдачи (next/prev)",
                "params": {
                    "direction": {"type": "string", "description": "next или prev", "default": "next"},
                    "search_engine": {"type": "string", "description": "google, yandex, auto", "default": "auto"}
                }
            },
            "close": {
                "description": "Закрывает браузер",
                "params": {}
            }
        }
    },
    "memory": {
        "description": "Долговременная память: сохранение фактов, поиск по прошлым диалогам",
        "actions": {
            "save": {
                "description": "Сохраняет факт в память",
                "params": {
                    "content": {"type": "string", "description": "Содержимое факта"},
                    "category": {"type": "string", "description": "user_info, solution, preference, skill, general", "default": "general"}
                },
                "required": ["content"]
            },
            "search": {
                "description": "Ищет релевантную информацию из прошлых диалогов",
                "params": {
                    "query": {"type": "string", "description": "Поисковый запрос"},
                    "limit": {"type": "integer", "description": "Макс. результатов", "default": 5}
                },
                "required": ["query"]
            },
            "summary": {
                "description": "Статистика по памяти (количество фактов, диалогов)",
                "params": {}
            },
            "cleanup": {
                "description": "Очищает устаревшие данные старше N дней",
                "params": {"days": {"type": "integer", "description": "Удалить старше N дней", "default": 30}}
            }
        }
    },
    "task": {
        "description": "Отслеживание задач: создание, попытки, выводы, статус",
        "actions": {
            "create": {
                "description": "Создаёт задачу для отслеживания",
                "params": {"description": {"type": "string", "description": "Описание задачи"}},
                "required": ["description"]
            },
            "add_attempt": {
                "description": "Фиксирует попытку с результатом",
                "params": {
                    "task_id": {"type": "integer"},
                    "actions_taken": {"type": "array", "items": {"type": "string"}},
                    "result": {"type": "string"},
                    "success": {"type": "boolean"},
                    "error_message": {"type": "string"}
                },
                "required": ["task_id", "actions_taken", "result", "success"]
            },
            "add_insight": {
                "description": "Сохраняет ключевой вывод",
                "params": {
                    "task_id": {"type": "integer"},
                    "content": {"type": "string"},
                    "insight_type": {"type": "string", "default": "learning"}
                },
                "required": ["task_id", "content"]
            },
            "update_status": {
                "description": "Обновляет статус (in_progress, completed, failed, blocked)",
                "params": {"task_id": {"type": "integer"}, "status": {"type": "string"}},
                "required": ["task_id", "status"]
            },
            "get_context": {
                "description": "Получает контекст задачи для продолжения",
                "params": {"task_id": {"type": "integer"}},
                "required": ["task_id"]
            },
            "list_incomplete": {
                "description": "Список незавершённых задач",
                "params": {}
            },
            "search_similar": {
                "description": "Ищет похожие успешные задачи",
                "params": {
                    "description": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["description"]
            }
        }
    },
    "result": {
        "description": "Сохранение и получение результатов (поиск, данные, списки)",
        "actions": {
            "save": {
                "description": "СОХРАНЯЕТ результат. ОБЯЗАТЕЛЬНО после поиска/извлечения данных!",
                "params": {
                    "result_type": {"type": "string", "description": "search_results, extracted_data, companies_list, contacts..."},
                    "content": {"type": "string", "description": "Содержимое (JSON)"},
                    "title": {"type": "string"},
                    "task_id": {"type": "integer"},
                    "ttl_hours": {"type": "integer", "default": 24}
                },
                "required": ["result_type", "content"]
            },
            "get": {
                "description": "Получает результат по ID",
                "params": {"result_id": {"type": "integer"}},
                "required": ["result_id"]
            },
            "list": {
                "description": "Список сохранённых результатов сессии",
                "params": {
                    "result_type": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                }
            },
            "get_latest": {
                "description": "Последний сохранённый результат",
                "params": {"result_type": {"type": "string"}}
            }
        }
    },
    "skill": {
        "description": "Навыки: специализированные инструкции и скрипты",
        "actions": {
            "get_info": {
                "description": "Получает полную информацию о навыке (инструкции, примеры)",
                "params": {"skill_name": {"type": "string"}},
                "required": ["skill_name"]
            },
            "run_script": {
                "description": "Выполняет скрипт из навыка",
                "params": {
                    "skill_name": {"type": "string"},
                    "script_name": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}, "default": []},
                    "timeout": {"type": "integer", "default": 60}
                },
                "required": ["skill_name", "script_name"]
            }
        }
    }
}


def get_core_tools() -> List[Dict[str, Any]]:
    """Returns core tools always available to the LLM."""
    return CORE_TOOLS.copy()


def get_registry_version() -> str:
    """Returns the current registry version."""
    return REGISTRY_VERSION


def get_registry_info() -> Dict[str, Any]:
    """Returns full registry information including version and stats."""
    return {
        "version": REGISTRY_VERSION,
        "core_tools_count": len(CORE_TOOLS),
        "extended_categories": len(EXTENDED_TOOLS),
        "total_extended_actions": sum(len(cat["actions"]) for cat in EXTENDED_TOOLS.values()),
        "categories": list(EXTENDED_TOOLS.keys())
    }


def get_tool_catalog() -> str:
    """Returns a compact catalog of available tool categories for the system prompt."""
    lines = ["Доступные категории инструментов (вызови tool_get_available(category) для деталей):"]
    for cat, info in EXTENDED_TOOLS.items():
        lines.append(f"- {cat}: {info['description']}")
    return "\n".join(lines)


def get_category_tools(category: str) -> Optional[Dict[str, Any]]:
    """Returns full info for a tool category."""
    return EXTENDED_TOOLS.get(category)


def list_categories() -> List[str]:
    """Returns all available category names."""
    return list(EXTENDED_TOOLS.keys())
