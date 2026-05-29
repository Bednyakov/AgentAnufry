# Настройка AgentAnufry для работы с Yandex Cloud

## Обзор

Этот документ описывает настройку агента для работы с Yandex Cloud Foundation Models API.

## Особенности Yandex Cloud

### Поддерживаемые функции
✅ **Chat Completions** - полностью поддерживается  
✅ **Function Calling** - поддерживается  
❌ **Embeddings API** - не поддерживается  

### Ограничения

1. **Embeddings**: Yandex Cloud не предоставляет API для embeddings, поэтому:
   - Семантический поиск в памяти агента будет отключен
   - Агент продолжит работать, но без возможности поиска похожих фактов
   - Все остальные функции памяти (сохранение, классификация важности) работают нормально

2. **Формат модели**: Модели указываются в формате URI:
   ```
   gpt://<folder_id>/<model_name>/<version>
   ```

## Конфигурация

### 1. Файл .env

```bash
# Провайдер
LLM_PROVIDER=openai

# API ключ от Yandex Cloud
LLM_API_KEY=your_yandex_api_key

# Базовый URL для Yandex Cloud
LLM_BASE_URL=https://ai.api.cloud.yandex.net/v1

# Модель в формате URI
LLM_MODEL=gpt://<folder_id>/<model_name>/latest

# Примеры моделей:
# - gpt://b1gpesajkrdn6fsfnhqq/deepseek-v4-flash/latest
# - gpt://b1gpesajkrdn6fsfnhqq/yandexgpt/latest
# - gpt://b1gpesajkrdn6fsfnhqq/yandexgpt-lite/latest

# Дополнительные параметры
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=300
MAX_ITERATIONS=20
```

### 2. Получение API ключа

1. Перейдите в [Yandex Cloud Console](https://console.cloud.yandex.ru/)
2. Выберите ваш каталог (folder)
3. Перейдите в раздел "API ключи"
4. Создайте новый API ключ для сервиса Foundation Models
5. Скопируйте ключ в `.env` файл

### 3. Определение Folder ID

Folder ID можно найти в URL консоли Yandex Cloud:
```
https://console.cloud.yandex.ru/folders/<folder_id>
```

## Исправленные ошибки

### Ошибка 1: "Failed to parse model URI"
**Причина**: Использовалась модель в неправильном формате  
**Решение**: Используйте формат `gpt://<folder_id>/<model_name>/latest`

### Ошибка 2: "Base64 encoding format is not supported"
**Причина**: Попытка использовать Embeddings API, который не поддерживается  
**Решение**: Embeddings автоматически отключены для Yandex Cloud

## Что работает

✅ Основной функционал агента  
✅ Выполнение команд shell  
✅ Работа с файлами  
✅ Управление браузером  
✅ Поиск в Google  
✅ Сохранение фактов в память  
✅ Классификация важности информации  
✅ Отслеживание задач  
✅ Система результатов  
✅ Навыки (skills)  

## Что не работает

❌ Семантический поиск в памяти (требует embeddings)  
❌ Поиск похожих задач по смыслу  
❌ Поиск похожих навыков по контексту  

## Альтернативы для Embeddings

Если вам нужен семантический поиск, рассмотрите следующие варианты:

### Вариант 1: Использовать OpenAI для embeddings
```bash
# В .env добавьте:
EMBEDDINGS_PROVIDER=openai
EMBEDDINGS_API_KEY=sk-your-openai-key
EMBEDDINGS_BASE_URL=https://api.openai.com/v1
EMBEDDINGS_MODEL=text-embedding-3-small
```

### Вариант 2: Локальные embeddings (в разработке)
```bash
# В .env добавьте:
EMBEDDINGS_PROVIDER=local
LOCAL_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Тестирование

После настройки запустите агента:

```bash
python main.py
```

Вы должны увидеть:
```
🔧 LLM Provider: openai
📡 Base URL: https://ai.api.cloud.yandex.net/v1
🤖 Model: gpt://b1gpesajkrdn6fsfnhqq/deepseek-v4-flash/latest
⚙️  Function Calling: ✓
```

Если появляются предупреждения об embeddings - это нормально:
```
⚠️ Ошибка получения embedding: ...
```

Агент продолжит работать без семантического поиска.

## Поддержка

Если у вас возникли проблемы:

1. Проверьте правильность API ключа
2. Убедитесь, что Folder ID указан верно
3. Проверьте формат модели (должен начинаться с `gpt://`)
4. Убедитесь, что у вас есть доступ к Foundation Models в Yandex Cloud

## Примеры использования

```python
# Агент работает как обычно
💬 Вы: Найди информацию о Python
⏳ Агент думает...
🤖 Агент: [выполняет поиск и отвечает]

# Память работает, но без семантического поиска
💬 Вы: Сохрани факт: я предпочитаю Python
⏳ Агент думает...
🤖 Агент: Факт сохранён в память (важность: 7/10)
```

## Changelog

- **2026-05-29**: Добавлена поддержка Yandex Cloud
- **2026-05-29**: Исправлены ошибки с embeddings и классификацией важности
- **2026-05-29**: Добавлена автоматическая детекция Yandex Cloud для отключения embeddings
