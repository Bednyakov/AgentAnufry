# Кроссплатформенная поддержка Shell

## Обзор

Агент Ануфрий теперь поддерживает работу на трёх операционных системах:
- **Linux** (bash)
- **macOS** (bash)
- **Windows** (cmd.exe)

Система автоматически определяет операционную систему и использует соответствующий shell для выполнения команд.

## Что изменилось

### 1. Автоматическое определение ОС

Добавлена функция `detect_os()` в `tools/shell.py`, которая определяет текущую ОС:
- `platform.system() == "Linux"` → `"linux"`
- `platform.system() == "Darwin"` → `"macos"`
- `platform.system() == "Windows"` → `"windows"`

### 2. Адаптивная конфигурация shell

Функция `get_shell_config()` возвращает правильный shell для каждой ОС:
- **Linux/macOS**: `/bin/bash`
- **Windows**: `cmd.exe`

### 3. ОС-специфичные опасные команды

Функция `get_dangerous_commands()` возвращает список опасных команд для текущей ОС:

**Linux/macOS:**
- `rm -rf /`
- `rm -rf /*`
- `mkfs.`
- `dd if=/dev/zero of=/dev/`
- `> /dev/sda`
- `:(){ :|:& };:` (fork bomb)

**Windows:**
- `format `
- `del /s /q c:\`
- `rd /s /q c:\`
- `rmdir /s /q c:\`
- `diskpart`
- `:(){ :|:& };:` (fork bomb)

### 4. Кроссплатформенные пути

В `config.py` обновлена переменная `WORKSPACE_DIR`:
```python
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.expanduser("~/agent-workspace"))
WORKSPACE_DIR = os.path.normpath(WORKSPACE_DIR)
```

Теперь пути автоматически нормализуются для текущей ОС:
- Linux/macOS: `/home/user/agent-workspace`
- Windows: `C:\Users\user\agent-workspace`

### 5. Информация об ОС в результатах

Все результаты выполнения команд теперь включают поле `"os"` с информацией о текущей ОС:
```json
{
  "success": true,
  "stdout": "...",
  "stderr": "",
  "returncode": 0,
  "os": "linux"
}
```

## Использование

### Базовое использование

Агент автоматически определяет ОС при запуске. Никаких дополнительных настроек не требуется:

```bash
# Linux/macOS
python main.py

# Windows
python main.py
```

### Примеры команд для разных ОС

**Linux/macOS:**
```python
run_shell("ls -la")
run_shell("grep 'pattern' file.txt")
run_shell("ps aux | grep python")
```

**Windows:**
```python
run_shell("dir")
run_shell("findstr 'pattern' file.txt")
run_shell("tasklist | findstr python")
```

### Кроссплатформенные команды

Некоторые команды работают одинаково на всех ОС:
```python
run_shell("python --version")
run_shell("git status")
run_shell("docker ps")
```

## Тестирование

Для проверки кроссплатформенной работы используйте тестовый скрипт:

```bash
# Linux/macOS
source .venv/bin/activate
python scripts/test_cross_platform.py

# Windows
.venv\Scripts\activate
python scripts\test_cross_platform.py
```

Тест проверяет:
1. ✓ Определение операционной системы
2. ✓ Выполнение базовых команд
3. ✓ Блокировку опасных команд
4. ✓ Работу с рабочей директорией

## Настройка рабочей директории

По умолчанию используется `~/agent-workspace`. Вы можете изменить это через переменную окружения:

**Linux/macOS:**
```bash
export WORKSPACE_DIR="/custom/path/to/workspace"
```

**Windows:**
```cmd
set WORKSPACE_DIR=C:\custom\path\to\workspace
```

Или в файле `.env`:
```
WORKSPACE_DIR=/custom/path/to/workspace
```

## Особенности работы на Windows

### Различия в командах

| Операция | Linux/macOS | Windows |
|----------|-------------|---------|
| Список файлов | `ls -la` | `dir` |
| Поиск в файлах | `grep pattern file` | `findstr pattern file` |
| Переменные окружения | `$HOME` | `%USERPROFILE%` |
| Разделитель путей | `/` | `\` |
| Процессы | `ps aux` | `tasklist` |

### Рекомендации для Windows

1. Используйте Python для кроссплатформенных операций:
   ```python
   run_shell("python -c \"import os; print(os.listdir('.'))\"")
   ```

2. Для работы с путями используйте `os.path` или `pathlib`:
   ```python
   import os
   path = os.path.join("folder", "file.txt")  # Работает везде
   ```

3. Избегайте Unix-специфичных команд (`grep`, `awk`, `sed`) на Windows

## Безопасность

Система блокирует опасные команды для каждой ОС автоматически. Попытка выполнить опасную команду вернёт ошибку:

```json
{
  "success": false,
  "stdout": "",
  "stderr": "Заблокирована потенциально опасная команда: rm -rf /",
  "returncode": 1,
  "os": "linux"
}
```

## Обратная совместимость

Все изменения полностью обратно совместимы с существующим кодом. Старые скрипты и команды продолжат работать без изменений на Linux.

## Известные ограничения

1. **PowerShell на Windows**: В данный момент используется `cmd.exe`. Для использования PowerShell потребуется дополнительная настройка.

2. **Bash на Windows**: Если у вас установлен Git Bash или WSL, вы можете настроить использование bash через переменные окружения.

3. **Специфичные команды**: Команды, специфичные для одной ОС (например, `apt` на Linux), не будут работать на других системах.

## Дальнейшее развитие

Планируемые улучшения:
- [ ] Поддержка PowerShell на Windows
- [ ] Автоматическая транслитерация команд между ОС
- [ ] Расширенная диагностика ошибок для каждой ОС
- [ ] Поддержка WSL (Windows Subsystem for Linux)

## Поддержка

Если вы обнаружили проблемы с кроссплатформенной работой:
1. Запустите тестовый скрипт: `python scripts/test_cross_platform.py`
2. Проверьте логи выполнения команд
3. Убедитесь, что используете правильный синтаксис команд для вашей ОС

## Примеры использования

### Пример 1: Проверка версии Python
```python
result = run_shell("python --version")
print(f"Python version on {result['os']}: {result['stdout']}")
```

### Пример 2: Кроссплатформенный список файлов
```python
import platform

if platform.system() == "Windows":
    result = run_shell("dir")
else:
    result = run_shell("ls -la")
```

### Пример 3: Работа с Git (кроссплатформенно)
```python
# Работает на всех ОС
run_shell("git status")
run_shell("git log --oneline -5")
run_shell("git branch")
```
