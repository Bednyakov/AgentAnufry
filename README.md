# AgentAnufry — Open Source AI Agent Framework на Python
Автономный AI-агент на Python с долговременной памятью, browser automation, task tracking и системой навыков.

```
AgentAnufry/
├── main.py                 # Gateway + Agent Loop
├── config.py               # Конфигурация
├── requirements.txt        # Зависимости Python
├── tools/
│   ├── shell.py            # Выполнение команд
│   ├── filesystem.py       # Работа с файлами
│   ├── browser.py          # Управление браузером через CDP
│   ├── memory_tools.py     # Инструменты памяти
│   ├── task_tools.py       # Инструменты трекера задач
│   ├── result_tools.py     # Инструменты работы с результатами
│   └── skills_runner.py    # Запуск навыков
├── memory/
│   ├── manager.py          # Менеджер долговременной памяти
│   ├── task_tracker.py     # Трекер задач
│   ├── task_results.py     # Менеджер результатов задач
│   ├── agent_memory.db     # SQLite база данных
│   └── README.md           # Документация памяти
├── skills/
│   ├── loader.py           # Загрузчик навыков
│   ├── README.md           # Документация навыков
│   └── mongo-compass/      # Пример навыка
│       ├── SKILL.md        # Описание навыка
│       ├── scripts/        # Скрипты навыка
│       └── references/     # Справочные материалы
├── docs/
│   ├── MEMORY_QUICKSTART.md      # Документация памяти
│   ├── TASK_TRACKING.md          # Документация трекера задач
│   ├── RESULTS_SYSTEM.md         # Система сохранения результатов
│   ├── SKILLS_ARCHITECTURE.md    # Архитектура навыков
│   └── GOOGLE_SEARCH_FIX.md      # Исправления поиска
├── llm/
│   ├── factory.py          # Фабрика для создания LLM провайдеров
│   └── provider.py         # Базовый класс для LLM провайдеров
└── ...
```
_____

# Запуск

## 1. Установка зависимостей
pip install -r requirements.txt

playwright install chromium

## 2. Настройка конфигурации
- скопируйте `.env.example` в `.env`
- выберите провайдера LLM (OpenAI, Ollama, LM Studio и др.)
- заполните конфигурацию:
    ```bash
    # Для OpenAI
    LLM_PROVIDER=openai
    LLM_API_KEY=sk-...
    LLM_MODEL=gpt-4
    
    # Для локальной Ollama
    LLM_PROVIDER=ollama
    LLM_MODEL=llama3.2
    ```
    - например, я ограничился таким .env:
    ```
    LLM_PROVIDER=openrouter
    LLM_API_KEY=sk-or-v1-...
    LLM_BASE_URL=https://openrouter.ai/api/v1
    LLM_MODEL=gpt-5
    ```
- подробнее см. [LOCAL_LLM_GUIDE.md](docs/LOCAL_LLM_GUIDE.md)

## 3. Запуск
python main.py
_____

## ✨ Новое:

Добавлена поддержка **локальных LLM**:

Агент теперь может работать с локальными языковыми моделями через OpenAI-совместимый API. Поддерживаются:
- 🏠 **Ollama** - простой запуск моделей локально
- 💻 **LM Studio** - GUI для управления моделями
- 🐳 **LocalAI** - self-hosted OpenAI API
- ⚡ **vLLM** - высокопроизводительный inference
- 🔧 **Text Generation WebUI** - oobabooga

Переключение между облачными и локальными моделями - одна строка в `.env`:
```bash
LLM_PROVIDER=ollama  # или openai, lmstudio, vllm и др.
```

**Подробнее:** см. [LOCAL_LLM_GUIDE.md](docs/LOCAL_LLM_GUIDE.md)
_____

Добавлена работа с **навыками**:

Система навыков позволяет агенту расширять свои возможности через модульные компоненты. Каждый навык — это самодостаточный модуль с инструкциями, скриптами и справочными материалами.

**Подробнее:** см. [SKILLS_ARCHITECTURE.md](docs/SKILLS_ARCHITECTURE.md)
_____

Агент имеет **долговременную память**:
- 🧠 Автоматически сохраняет важные диалоги и факты
- 🔍 Семантический поиск через OpenAI embeddings
- 🎯 Автоматическая классификация важности информации
- 🧹 Умная очистка устаревших данных
- 💾 Персистентность между сессиями

Похвалите агента, если он успешно справился с тяжелой задачей. Он оптимизирует алгоритм действий и сохранит в долговременную память. И в следующий раз справится с задачей значительно быстрее:

    ```
    🤖 Агент: Супер, Артём! Я сохранил оптимальный алгоритм выполнения этой задачи в долговременную память. В следующий раз смогу повторить процесс быстрее и без лишних действий.
    ```

**Подробнее:** см. [MEMORY_QUICKSTART.md](docs/MEMORY_QUICKSTART.md)
______

Агент имеет **трекер задач**:

- Не теряется контекст: помнит все попытки и ошибки 

- Экономия памяти: сохраняется только важная информация 

- Возможность повтора: можно продолжить с любого момента 

- База знаний: успешные решения используются для похожих задач 

- Отладка: легко понять, где возникла проблема

Ануфрий эффективно работает со сложными задачами, не засоряя память и сохраняя возможность продолжить работу в любой момент!

**Подробнее:** см. [TASK_TRACKING.md](docs/TASK_TRACKING.md)
______

Агент имеет **систему сохранения результатов**:

- 💾 Автоматически сохраняет результаты поиска и извлечения данных
- 🔄 Использует результаты в последующих запросах без повторного поиска
- 📊 Показывает доступные результаты в контексте
- ⏰ Автоматически очищает устаревшие результаты (TTL)
- 🎯 Связывает результаты с задачами

Теперь когда вы просите "Найди компании" → "Сохрани в файл", агент НЕ будет искать заново, а использует сохранённые результаты!

**Подробнее:** см. [RESULTS_SYSTEM.md](docs/RESULTS_SYSTEM.md)
_____

# От автора
**Основная идея проекта** - дать инженерам и энтузиастам простую базовую кострукцию мультизадачного агента с т.н. искусственным интеллектом для пробуждения интереса к теме разработки ИИ-агентов на базе больших языковых моделей.

Структура максимально упрощена, чтобы вы могли за незначительное время переработать модули агента частично или полностью: 
- заменить БД или изменить правила работы с памятью
- усовершенствовать или переписать встроенные навыки
- добавить новые инструменты для работы в интернете
- улучшить обработку модульных скиллов
- оптимизировать работу с LLM

Все в ваших руках. Прокачивайте Ануфрия до стостояния киборга, помноженного на вечность, фантазируйте, и воплощайте в жизнь. Делайте форки или предлагайте пул реквесты для улучшения этого проекта.

Похвастаться своими результатами, сообщить о багах, обсудить проект или связаться со мной вы можете в [Telegram](https://t.me/itpolice)

Если проект оказался вам полезен, поставьте ему звездочку ⭐️. Спасибо!

С уважением, Бедняков Тема.

__
# Пример работы

```
==================================================
🤖 Агент Ануфрий с доступом к shell (Ctrl+C для выхода)
==================================================

💬 Вы: Покажи содержимое текущей директории

⏳ Агент думает...

--- Итерация 1 ---
🔧 Вызов: list_dir({"path": "."})
📤 Результат: {"success": true, "items": [...]}

🤖 Агент: В рабочей директории находятся следующие файлы: ...

💬 Вы: Установи mongosh и проверь подключение к localhost:27017

⏳ Агент думает...

--- Итерация 1 ---
🔧 Вызов: run_shell({"command": "which mongosh || sudo apt install -y mongodb-mongosh"})
📤 Результат: {"success": true, "stdout": "/usr/bin/mongosh", ...}

--- Итерация 2 ---
🔧 Вызов: run_shell({"command": "mongosh \"mongodb://localhost:27017\" --eval \"db.adminCommand('ping')\""})
📤 Результат: {"success": true, "stdout": "{ ok: 1 }", ...}

🤖 Агент: MongoDB Shell установлен. Подключение к localhost:27017 успешно — сервер отвечает { ok: 1 }.
```

_____
## SEO

---

# AI Agent Framework на Python — Open Source Multi-Agent Assistant

**AgentAnufry** — open source AI agent framework на Python для создания автономных LLM-агентов с долговременной памятью, системой навыков, трекером задач и управлением браузером через CDP/Playwright.

Проект подходит для:
- разработки AI-агентов на Python
- создания autonomous agents
- LLM orchestration
- AI assistants
- browser automation
- agentic workflows
- memory-driven AI systems
- AI task automation
- local AI agents
- multi-tool AI systems

### Ключевые возможности

- 🧠 Long-term memory для AI-агента
- 🌐 Browser automation через Chrome DevTools Protocol
- 🛠 Расширяемая skill-based architecture
- 📂 Работа с файлами и shell-командами
- 📋 Task tracking и сохранение промежуточных результатов
- 🔍 Семантический поиск через embeddings
- 💾 SQLite persistence layer
- ⚡ Lightweight Python AI agent framework
- 🔌 Простое расширение через Python-модули

### SEO Keywords

AI agent Python, autonomous AI agent, Python AI framework, open source AI agent, LLM agent framework, browser AI agent, multi-agent system Python, AI assistant Python, long-term memory AI, AI automation framework, agentic AI, local AI agent, AI orchestration, Playwright AI automation, Chrome DevTools Protocol AI, semantic memory AI, GPT agent Python, modular AI agent architecture, AI tools framework, task-oriented AI system.

### Подходит для

- AI engineering
- backend developers
- AI research experiments
- automation engineers
- LLM enthusiasts
- self-hosted AI solutions
- experimental AI systems
- agent-based architectures

---