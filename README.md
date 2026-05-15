# OpenAnufry
Российский агент Ануфрий на Python

```
agent-Anufry/
├── main.py              # Gateway + Agent Loop
├── tools/
│   ├── shell.py         # Выполнение команд
│   ├── filesystem.py    # Работа с файлами
│   └── browser.py       # Управление браузером через CDP
├── config.py            # Конфигурация
└── requirements.txt
```


# Запуск

## 1. Установка зависимостей
pip install -r requirements.txt
playwright install chromium

## 2. Настройка API-ключа
export OPENAI_API_KEY="sk-..."

## 3. Запуск
python main.py


# Пример работы

```
==================================================
🤖 Агент с доступом к shell (Ctrl+C для выхода)
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
