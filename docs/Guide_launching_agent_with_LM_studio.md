# Быстрый запуск агента на локальной модели с LM Studio на Linux

1. Для быстрого запуска нам хватит безголового (без графического интерфейса) демона llmster (https://lmstudio.ai/).
Команда в терминале:
```bash
curl -fsSL https://lmstudio.ai/install.sh | bash
```
2. Перезапустите терминал или добавьте директорию lms командой, которую покажут в терминале.

3. Запускаем
```bash
lms daemon up
```

4. Качаем нужную LLM модель (чем больше, тем умнее, но требует больше ресурсов): https://lmstudio.ai/models
Для примера возьмем небольшую модель:
```bash
lms get qwen/qwen3.5-9b
```

5. После скачивания подгружаем модель в память:
```bash
lms load qwen/qwen3.5-9b
```

6. В .env скопируйте эту конфигурацию:
```
# ============================================
# LM Studio Configuration (Local) - ACTIVE
# ============================================
LLM_PROVIDER=lmstudio
LLM_API_KEY=lm-studio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=deepseek/deepseek-r1-0528-qwen3-8b

# ============================================
# Embeddings Configuration (Local) - ACTIVE
# ============================================
# Используем локальную embeddings модель из LM Studio
EMBEDDINGS_PROVIDER=lmstudio
EMBEDDINGS_MODEL=text-embedding-nomic-embed-text-v1.5
EMBEDDINGS_BASE_URL=http://localhost:1234/v1
EMBEDDINGS_API_KEY=lm-studio

# ============================================
# Дополнительные параметры
# ============================================
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=300
MAX_ITERATIONS=20
```

7. Запустите lms сервер:
```bash
lms server start --port 1234 &
```
или
```
lms server start
```
Порт по умолчанию будет 1234

8. Запустите агента.


### Шпаргалка с командами lms
```
# запустить демон
lms daemon up

# запуск/остановка сервера
lms server start
lms server stop

lms server status        # статус сервера
lms ps                   # загруженные в память модели
lms ls                   # список скачанных моделей

# остановить текущую модель
lms unload

# выгрузить все модели из памяти
lms unload --all

# получить список доступных моделей
lms ls

# Удалить конкретную модель
lms rm qwen/qwen3.5-9b

# Или удалить несколько моделей
lms rm model1 model2 model3

```

## Важно!
Чем слабее ваше железо, тем меньше модель вы сможете использовать, с меньшим объемом контекстного окна.
Объем контекста в базовой версии агента (системный промпт + описание инструментов) в районе 6к товенов, это много.
Для работы с небольшими моделями сожмите системный промпт и описание инструментов или удалите лишнее (файл main.py)

### Пример

```
SYSTEM_PROMPT_MINI = f"""Ты — агент с доступом к Linux-системе и долговременной памятью.

Инструменты:
- run_shell, read_file, write_file, list_dir — работа с системой и файлами
- browser_search_google, browser_extract_content — поиск и извлечение контента
- memory_save_fact, memory_search — сохранение и поиск в памяти
- task_create, task_add_attempt, task_update_status — отслеживание задач
- result_save, result_get_latest — сохранение и получение результатов
- skill_get_info, skill_run_script — работа с навыками

Правила работы с поиском:
- Используй browser_search_google для поиска
- Затем browser_extract_content для получения полного контента со страниц
- Сохраняй результаты через result_save

Правила работы с результатами:
- Всегда сохраняй важные данные через result_save
- Перед повторным поиском проверяй result_get_latest
- Не дублируй поиск если данные уже сохранены

Правила работы с памятью:
- Сохраняй важную информацию через memory_save_fact
- Используй memory_search для поиска в прошлых диалогах

Правила работы с задачами:
- Для сложных задач создавай task_create
- Фиксируй попытки через task_add_attempt
- Обновляй статус через task_update_status

{SKILLS_CATALOG}

Общие правила:
- Разбивай сложные задачи на шаги
- Читай вывод команд перед следующим действием
- Не выполняй опасные команды без подтверждения

Рабочая директория: ~/agent-workspace
"""


TOOLS_MINI = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Выполняет shell-команду на Linux-машине.",
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
            "description": "Открывает URL в браузере.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL"}
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
            "description": "Поиск в Google. Возвращает список результатов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_extract_content",
            "description": "Извлекает контент со страницы. Используй после browser_search_google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL страницы"},
                    "selectors": {"type": "array", "items": {"type": "string"}, "description": "CSS селекторы", "default": None}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_navigate_search_page",
            "description": "Навигация по страницам поисковой выдачи.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "description": "'next' или 'prev'", "default": "next"},
                    "search_engine": {"type": "string", "description": "'google', 'yandex', 'auto'", "default": "auto"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_save_fact",
            "description": "Сохраняет важный факт в память.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Содержимое факта"},
                    "category": {"type": "string", "description": "Категория", "default": "general"}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Ищет информацию в памяти.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Запрос"},
                    "limit": {"type": "integer", "description": "Лимит результатов", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_get_summary",
            "description": "Статистика памяти.",
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
            "description": "Очищает устаревшие данные.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Старше N дней", "default": 30}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_create",
            "description": "Создаёт задачу для отслеживания.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Описание"}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_add_attempt",
            "description": "Фиксирует попытку выполнения.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"},
                    "actions_taken": {"type": "array", "items": {"type": "string"}, "description": "Действия"},
                    "result": {"type": "string", "description": "Результат"},
                    "success": {"type": "boolean", "description": "Успех"},
                    "error_message": {"type": "string", "description": "Ошибка"}
                },
                "required": ["task_id", "actions_taken", "result", "success"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_add_insight",
            "description": "Добавляет вывод из задачи.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "ID задачи"},
                    "content": {"type": "string", "description": "Содержание"},
                    "insight_type": {"type": "string", "description": "Тип", "default": "learning"}
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
            "description": "Получает контекст задачи.",
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
            "description": "Список незавершённых задач.",
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
            "description": "Ищет похожие задачи.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Описание"},
                    "limit": {"type": "integer", "description": "Лимит", "default": 5}
                },
                "required": ["description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_save",
            "description": "Сохраняет результат. Используй после получения важных данных.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_type": {"type": "string", "description": "Тип результата"},
                    "content": {"type": "string", "description": "Содержимое в JSON"},
                    "title": {"type": "string", "description": "Заголовок"},
                    "task_id": {"type": "integer", "description": "ID задачи"},
                    "ttl_hours": {"type": "integer", "description": "Время жизни в часах", "default": 24}
                },
                "required": ["result_type", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_get",
            "description": "Получает результат по ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_id": {"type": "integer", "description": "ID"}
                },
                "required": ["result_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_list",
            "description": "Список сохранённых результатов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_type": {"type": "string", "description": "Фильтр по типу"},
                    "limit": {"type": "integer", "description": "Лимит", "default": 10}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "result_get_latest",
            "description": "Получает последний результат.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result_type": {"type": "string", "description": "Фильтр по типу"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skill_get_info",
            "description": "Получает информацию о навыке.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "Название навыка"}
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "skill_run_script",
            "description": "Выполняет скрипт из навыка.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "Навык"},
                    "script_name": {"type": "string", "description": "Скрипт"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Аргументы", "default": []},
                    "timeout": {"type": "integer", "description": "Таймаут", "default": 60}
                },
                "required": ["skill_name", "script_name"]
            }
        }
    }
]
```