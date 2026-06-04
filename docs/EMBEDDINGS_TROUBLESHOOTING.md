# Решение проблем с Embeddings и семантическим поиском

## Проблема

После настройки Yandex Cloud в качестве основной LLM модели, семантический поиск в памяти агента, ожидаемо, перестал работать.

## Причина

API Yandex Cloud не поддерживает embeddings API

## Решение

### 1. Добавить дополнительные настройки в `.env` для работы с ebbeddings через Openrouter

```env
EMBEDDINGS_PROVIDER=openrouter
EMBEDDINGS_MODEL=text-embedding-3-small  # ✅ Правильная embedding модель
EMBEDDINGS_BASE_URL=https://openrouter.ai/api/v1
EMBEDDINGS_API_KEY=your-openrouter-api-key
```
### Важно
Не все модели доступны для embeddings.
Например, Модель `gpt-4-mini` - это модель для генерации текста (chat completions), а не для создания векторных представлений (embeddings). При попытке получить embedding с такой моделью возникнет ошибка. В консоль будет выведено сообщение, что отключен семантический поиск.

### 2. Доступные модели для embeddings

#### OpenRouter / OpenAI
- `text-embedding-3-small` - быстрая и эффективная (рекомендуется)
- `text-embedding-3-large` - более точная, но медленнее
- `text-embedding-ada-002` - старая версия

#### Важно
OpenRouter проксирует запросы к OpenAI для embeddings, поэтому используйте модели OpenAI.

### 3. Проверка работы

Запустите тестовый скрипт:

```bash
python3 scripts/test_embeddings.py
```

Вы должны увидеть:
- ✅ Успешное получение embeddings
- ✅ Размерность вектора (обычно 1536 для text-embedding-3-small)
- ✅ Результаты семантического поиска с показателями сходства

## Альтернативные решения

### Вариант 1: Использовать OpenAI напрямую

Если у вас есть ключ OpenAI:

```env
EMBEDDINGS_PROVIDER=openai
EMBEDDINGS_MODEL=text-embedding-3-small
EMBEDDINGS_BASE_URL=https://api.openai.com/v1
EMBEDDINGS_API_KEY=sk-your-openai-key
```

### Вариант 2: Локальные embeddings (в разработке)

Для работы без внешних API можно использовать локальные embeddings:

```env
EMBEDDINGS_PROVIDER=local
LOCAL_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**Примечание:** Требуется установка `sentence-transformers`:
```bash
pip install sentence-transformers
```

## Как работает семантический поиск

1. **Создание embeddings**: Текст преобразуется в вектор чисел (обычно 1536 измерений)
2. **Хранение**: Векторы сохраняются в SQLite вместе с текстом
3. **Поиск**: При запросе создается embedding запроса и вычисляется косинусное сходство со всеми сохраненными векторами
4. **Ранжирование**: Результаты сортируются по степени сходства

## Диагностика проблем

### Проверка конфигурации

```bash
grep EMBEDDINGS .env
```

### Проверка логов

При ошибках embeddings в консоли появится сообщение:
```
⚠️ Ошибка получения embedding (модель: ..., провайдер: ...): [детали ошибки]
```

### Типичные ошибки

1. **Неправильная модель**: Используется chat модель вместо embedding модели
2. **Неверный API ключ**: Проверьте `EMBEDDINGS_API_KEY`
3. **Провайдер не поддерживает embeddings**: Некоторые провайдеры (например, Ollama) требуют дополнительной настройки

## История изменений

- **2026-05-29**: Добавлена поддержка отдельной конфигурации для embeddings
- **2026-06-04**: Исправлена проблема с неправильной моделью в конфигурации

## Дополнительная информация

- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Sentence Transformers](https://www.sbert.net/)
